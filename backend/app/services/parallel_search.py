import asyncio
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
from parallel import Parallel

from backend.app.agents.director_agent import Scene
from backend.app.schemas.location import LocationRequirements

load_dotenv()

# Logging.getLogger() uses a hierarchical tree structure by dots
logger = logging.getLogger(__name__)

def compact_search_region(region: str) -> str:
    """
    Convert a detailed address into a concise search region.

    Examples:
        "200 Broadway, New York, NY 10038, USA"
        becomes:
        "New York"

        "Bratislava, Slovakia"
        becomes:
        "Bratislava"
    """

    normalized_region = " ".join(region.split())

    parts = [
        part.strip()
        for part in normalized_region.split(",")
        if part.strip()
    ]

    if not parts:
        return normalized_region

    first_part_contains_number = any(
        character.isdigit()
        for character in parts[0]
    )

    # If the first part looks like a street address,
    # the second part is normally the city.
    if first_part_contains_number and len(parts) >= 2:
        return parts[1]

    # Otherwise, use the first region component.
    return parts[0]


def clean_fallback_venue_term(value: str) -> str:
    """
    Remove screenplay formatting from a fallback venue description.

    Example:
        "INT. ABANDONED TRAIN PLATFORM - NIGHT"
        becomes:
        "abandoned train platform"
    """

    cleaned_value = re.sub(
        r"\b(?:INT|EXT|INT/EXT|EXT/INT)\b\.?",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # Remove screenplay time-of-day information.
    cleaned_value = re.split(
        r"\s+-\s+",
        cleaned_value,
        maxsplit=1,
    )[0]

    cleaned_value = " ".join(
        cleaned_value.split()
    ).strip()

    if not cleaned_value:
        return "filming location"

    # Keep fallback searches concise.
    words = cleaned_value.split()

    return " ".join(words[:4]).lower()


def get_search_venue_terms(
    scene: Scene,
) -> tuple[str, str]:
    """
    Convert screenplay descriptions into common web-search terms.

    Returns:
        A primary venue term and an alternative venue term.
    """

    scene_text = " ".join(
        filter(
            None,
            [
                scene.location_setting,
                scene.scene_heading,
            ],
        )
    ).lower()

    venue_mapping = [
        (
            ("cafe", "café", "coffee shop"),
            ("cafe", "coffee shop"),
        ),
        (
            ("restaurant", "diner"),
            ("restaurant", "dining venue"),
        ),
        (
            ("office", "workplace"),
            ("office", "office space"),
        ),
        (
            ("hospital", "medical center", "clinic"),
            ("hospital", "medical facility"),
        ),
        (
            ("warehouse", "industrial building"),
            ("warehouse", "industrial venue"),
        ),
        (
            ("apartment", "flat"),
            ("apartment", "residential interior"),
        ),
        (
            ("house", "home", "residence"),
            ("house", "residential property"),
        ),
        (
            ("bar", "pub", "nightclub"),
            ("bar", "nightlife venue"),
        ),
        (
            ("hotel", "motel"),
            ("hotel", "hospitality venue"),
        ),
        (
            ("school", "classroom", "university"),
            ("school", "education venue"),
        ),
        (
            ("alley", "backstreet"),
            ("urban alley", "city alley"),
        ),
        (
            ("rooftop", "roof terrace"),
            ("rooftop", "roof terrace"),
        ),
        (
            ("park", "garden"),
            ("public park", "outdoor garden"),
        ),
        (
            ("theater", "theatre", "auditorium"),
            ("theater", "performance venue"),
        ),
        (
            ("church", "chapel"),
            ("church", "religious venue"),
        ),
        (
            ("airport", "terminal"),
            ("airport terminal", "aviation venue"),
        ),
        (
            ("train station", "railway station"),
            ("train station", "railway platform"),
        ),
        (
            ("subway", "metro station"),
            ("subway station", "metro platform"),
        ),
        (
            ("beach", "coast"),
            ("beach", "coastal location"),
        ),
        (
            ("forest", "woods"),
            ("forest", "woodland location"),
        ),
        (
            ("farm", "barn"),
            ("farm", "rural property"),
        ),
    ]

    for keywords, search_terms in venue_mapping:
        if any(
            keyword in scene_text
            for keyword in keywords
        ):
            return search_terms

    fallback_value = (
        scene.location_setting
        or scene.scene_heading
        or "filming location"
    )

    fallback_term = clean_fallback_venue_term(
        fallback_value
    )

    return fallback_term, fallback_term


def build_search_objective(
    scene: Scene,
    requirements: LocationRequirements,
) -> str:
    """
    Build a focused and self-contained Parallel Search objective.

    The objective tells Parallel what evidence should be prioritized.
    It does not replace the Location Agent's final evaluation.
    """

    primary_venue, alternative_venue = (
        get_search_venue_terms(scene)
    )

    effective_environment = (
        requirements.environment
        if requirements.environment != "Either"
        else scene.interior_exterior
    )

    visual_features = (
        ", ".join(scene.location_features)
        if scene.location_features
        else "No specific visual features documented"
    )

    production_requirements = (
        ", ".join(scene.shooting_requirements)
        if scene.shooting_requirements
        else "No special production requirements"
    )

    additional_requirements = (
        requirements.additional_requirements.strip()
        if requirements.additional_requirements.strip()
        else "None"
    )

    filming_date = (
        requirements.filming_date.isoformat()
        if requirements.filming_date
        else "Not specified"
    )

    if requirements.location_type == "practical":
        location_type_instruction = (
            "Find practical, real-world venues. Exclude ordinary "
            "photo studios and lifestyle lofts unless the page "
            "clearly documents a permanent physical environment "
            "matching the required venue."
        )

    elif requirements.location_type == "studio":
        location_type_instruction = (
            "Find studios or purpose-built production sets that "
            "explicitly reproduce the required physical environment."
        )

    else:
        location_type_instruction = (
            "Both practical venues and purpose-built studio sets "
            "are acceptable. The source should make the location "
            "type identifiable."
        )

    return f"""
Find identifiable filming-location candidates for a {primary_venue} or
compatible {alternative_venue} near {requirements.preferred_region}.

SCENE NEEDS

- Scene: {scene.scene_heading}
- Required venue type: {primary_venue}
- Compatible venue term: {alternative_venue}
- Required environment: {effective_environment}
- Visual and architectural features: {visual_features}
- Production requirements: {production_requirements}
- Additional user requirements: {additional_requirements}

USER CONSTRAINTS

- Search center: {requirements.preferred_region}
- Maximum distance: {requirements.maximum_distance_km} km
- Maximum day rate: {requirements.maximum_day_rate}
  {requirements.currency}
- Permit preference: {requirements.permit_preference}
- Preferred filming date: {filming_date}

LOCATION-TYPE REQUIREMENT

{location_type_instruction}

SOURCE PRIORITIES

Prioritize:

1. Dedicated pages for individual venues.
2. Individual film-location or production-rental listings.
3. Official venue websites mentioning filming, production, private rental,
   events, or commercial photography.
4. Reputable location directories and film-commission listings.

Each result should identify one named venue or property whenever possible.

VENUE VERIFICATION

Do not treat a word appearing in a business name as proof of venue type.
Verify the venue type using the page category, description, documented
physical features, or photographs.

For example, a business named "Cafe Studio" is not necessarily an actual
cafe. A normal loft or photo studio should not be presented as a cafe
unless its description or images document a cafe environment.

EVIDENCE TO RETRIEVE

Prefer pages containing evidence about:

- actual venue category;
- physical and architectural appearance;
- address or identifiable area;
- filming, production, event, or private-rental use;
- advertised price and price unit;
- capacity;
- production amenities;
- equipment and crew access;
- permits;
- availability;
- photographs or gallery links.

AVOID

Avoid general travel articles, unnamed properties, generic search-result
pages, and list articles that provide no usable information about an
individual venue.

Missing price, permit, capacity, or availability information should remain
unknown. Do not remove an otherwise relevant venue solely because one of
these details is not publicly documented.
""".strip()


def build_search_queries(
    scene: Scene,
    requirements: LocationRequirements,
) -> list[str]:
    """
    Build three concise and diverse search queries.

    Detailed constraints belong in the objective. Search queries
    should concentrate on discovering relevant webpages.
    """

    region = compact_search_region(
        requirements.preferred_region
    )

    primary_venue, alternative_venue = (
        get_search_venue_terms(scene)
    )

    if requirements.location_type == "studio":
        queries = [
            f"{primary_venue} film set {region}",
            f"{alternative_venue} studio rental {region}",
            f"{primary_venue} production set {region}",
        ]

    elif requirements.location_type == "practical":
        queries = [
            f"{primary_venue} filming rental {region}",
            f"{alternative_venue} production venue {region}",
            f"{primary_venue} private rental {region}",
        ]

    else:
        queries = [
            f"{primary_venue} filming rental {region}",
            f"{alternative_venue} production venue {region}",
            f"{primary_venue} film set {region}",
        ]

    # Remove duplicate queries while preserving their order.
    return list(dict.fromkeys(queries))


def execute_parallel_search(
    objective: str,
    search_queries: list[str],
) -> Any:
    """
    Execute the blocking Parallel SDK request.

    This function is run in a worker thread so the synchronous
    Parallel SDK does not block FastAPI's event loop.
    """

    api_key = os.getenv("PARALLEL_API_KEY")

    if not api_key:
        raise RuntimeError(
            "PARALLEL_API_KEY is missing."
        )

    client = Parallel(api_key=api_key)

    return client.search(
        objective=objective,
        search_queries=search_queries,
        mode="advanced",
        max_chars_total=30_000,
    )


def normalize_search_results(
    search_response: Any,
) -> list[dict[str, Any]]:
    """
    Convert Parallel result objects into JSON-serializable dictionaries.

    This function also:
    - removes results without URLs;
    - removes duplicate URLs;
    - removes results without usable excerpts.
    """

    normalized_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    search_results = getattr(
        search_response,
        "results",
        None,
    ) or []

    for result in search_results:
        raw_url = getattr(
            result,
            "url",
            None,
        )

        if not raw_url:
            continue

        url = str(raw_url).strip()

        if not url:
            continue

        # Treat URLs with and without a final slash as duplicates.
        normalized_url = url.rstrip("/")

        if normalized_url in seen_urls:
            continue

        raw_excerpts = getattr(
            result,
            "excerpts",
            None,
        ) or []

        excerpts = [
            str(excerpt).strip()
            for excerpt in raw_excerpts
            if str(excerpt).strip()
        ]

        # Without excerpts, the Location Agent has no evidence
        # with which to evaluate the source.
        if not excerpts:
            continue

        raw_title = getattr(
            result,
            "title",
            None,
        )

        title = (
            str(raw_title).strip()
            if raw_title
            else "Untitled location source"
        )

        seen_urls.add(normalized_url)

        normalized_results.append(
            {
                "title": title,
                "url": url,
                "excerpts": excerpts,
            }
        )

    return normalized_results


def log_search_results(
    objective: str,
    search_queries: list[str],
    results: list[dict[str, Any]],
) -> None:
    """
    Log the Parallel request and normalized results.

    The print output is intentionally visible in the backend terminal
    while developing and testing the location pipeline.
    """

    logger.info(
        "Parallel location objective:\n%s",
        objective,
    )

    logger.info(
        "Parallel search queries: %s",
        search_queries,
    )

    logger.info(
        "Parallel returned %s usable source pages.",
        len(results),
    )

    print("\n========== PARALLEL SEARCH ==========")
    print("\nSEARCH QUERIES")

    for index, query in enumerate(
        search_queries,
        start=1,
    ):
        print(f"{index}. {query}")

    print(
        f"\nUSABLE RESULTS: {len(results)}"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):
        print(f"\nRESULT {index}")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")

        for excerpt_index, excerpt in enumerate(
            result["excerpts"],
            start=1,
        ):
            print(
                f"Excerpt {excerpt_index}: {excerpt}"
            )

    print("\n=====================================")


async def search_location_candidates(
    scene: Scene,
    requirements: LocationRequirements,
) -> list[dict[str, Any]]:
    """
    Search for filming-location source pages using:

    1. Scene information produced by the Director Agent.
    2. Location requirements supplied by the user.
    3. Current public webpages retrieved through Parallel Search.
    """

    objective = build_search_objective(
        scene=scene,
        requirements=requirements,
    )

    search_queries = build_search_queries(
        scene=scene,
        requirements=requirements,
    )

    if not search_queries:
        raise RuntimeError(
            "No location search queries could be generated."
        )

    try:
        search_response = await asyncio.to_thread(
            execute_parallel_search,
            objective,
            search_queries,
        )

    except Exception as error:
        logger.exception(
            "Parallel location search failed."
        )

        raise RuntimeError(
            f"Parallel location search failed: {error}"
        ) from error

    results = normalize_search_results(
        search_response
    )

    log_search_results(
        objective=objective,
        search_queries=search_queries,
        results=results,
    )

    if not results:
        raise RuntimeError(
            "Parallel Search returned no usable location sources."
        )

    return results