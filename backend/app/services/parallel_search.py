import asyncio
import logging
import os
import re
import time
from typing import Any

from dotenv import load_dotenv
from parallel import Parallel

from backend.app.agents.director_agent import Scene
from backend.app.schemas.location import LocationRequirements

load_dotenv()

# Logging.getLogger() uses a hierarchical tree structure by dots
logger = logging.getLogger(__name__)

# Domains that reliably produce generic, unnamed, or low-signal pages
# for filming-location discovery. Excluded at the API level rather than
# just told to the model, since a soft instruction can be ignored.
LOW_QUALITY_DOMAINS = [
    "pinterest.com",
    "reddit.com",
    "quora.com",
    "tripadvisor.com",
]

# The model that consumes the Location Agent's search results. Passed to
# Parallel as client_model so excerpts are formatted for this model.
LOCATION_AGENT_MODEL = "gemini-3.5-flash-lite"

# Bounded retry settings for execute_parallel_search(), to absorb
# transient network/API failures.
MAX_SEARCH_ATTEMPTS = 2
RETRY_BACKOFF_SECONDS = 1.5

# Best-effort country-name to ISO alpha-2 mapping, used to geo-bias
# search results toward the right country when we can confidently parse
# one out of the user's preferred_region. Deliberately conservative:
# if a region doesn't end in a recognized country name, we omit the
# location bias entirely rather than guess, since an incorrect or
# overly restrictive location setting can reduce result quality rather
# than improve it.
_COUNTRY_TO_ISO2 = {
    "usa": "us",
    "us": "us",
    "united states": "us",
    "united states of america": "us",
    "uk": "gb",
    "united kingdom": "gb",
    "canada": "ca",
    "australia": "au",
    "germany": "de",
    "france": "fr",
    "spain": "es",
    "italy": "it",
    "ireland": "ie",
    "new zealand": "nz",
}


def guess_country_code(region: str) -> str | None:
    """
    Best-effort extraction of an ISO alpha-2 country code from the
    user's preferred_region, used only to bias search geography.

    Returns None (no bias applied) when the country can't be
    confidently identified from the final comma-separated segment,
    rather than guessing.
    """

    parts = [
        part.strip().lower()
        for part in region.split(",")
        if part.strip()
    ]

    if not parts:
        return None

    return _COUNTRY_TO_ISO2.get(parts[-1])


def compact_search_region(region: str) -> str:
    """
    Convert a detailed address into a search-friendly region
    without losing too much geographic context.

    Example:
        "200 Broadway, New York, NY 10038, USA"
        -> "New York City, NY"
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

    # Full street address:
    # "200 Broadway, New York, NY 10038, USA"
    if first_part_contains_number and len(parts) >= 3:
        city = parts[1]
        state = parts[2]

        # Special case because "New York" is ambiguous in search.
        if city.lower() == "new york":
            return "New York City, NY"

        return f"{city}, {state}"

    # User entered something like:
    # "New York, NY, USA"
    if len(parts) >= 2:
        city = parts[0]
        state = parts[1]

        if city.lower() == "new york":
            return "New York City, NY"

        return f"{city}, {state}"

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


def get_visual_search_terms(
    scene: Scene,
    max_features: int = 1,
) -> str:
    """
    Return a small number of screenplay-derived visual features
    that are useful for venue discovery.

    We intentionally keep this short (default: a single feature)
    so each search query stays within Parallel's recommended
    3-6 word range for keyword queries.
    """

    features = [
        feature.strip()
        for feature in scene.location_features
        if feature.strip()
    ]

    return " ".join(features[:max_features])


def build_search_objective(
    scene: Scene,
    requirements: LocationRequirements,
) -> str:
    """
    Build a concise, natural-language search objective.

    Parallel's Search API is tuned to parse a short natural-language
    goal naming the key entity/topic, not a long structured document
    with headers and bullet lists. Keep this to a couple of sentences.
    """

    primary_venue, _ = get_search_venue_terms(scene)

    effective_environment = (
        requirements.environment
        if requirements.environment != "Either"
        else scene.interior_exterior
    )

    visual_features = (
        ", ".join(scene.location_features[:3])
        if scene.location_features
        else "no specific visual features documented"
    )

    additional_requirements = (
        requirements.additional_requirements.strip()
        if requirements.additional_requirements.strip()
        else "none"
    )

    return (
        f"Find real, individually named {primary_venue} venues near "
        f"{requirements.preferred_region} suitable for a "
        f"{effective_environment.lower()} filming scene with these "
        f"features: {visual_features}. Additional requirements: "
        f"{additional_requirements}. Prefer official venue pages and "
        f"individual rental listings that name a specific place; avoid "
        f"generic articles or unnamed properties. Also avoid "
        f"multi-category roundup articles that group different kinds "
        f"of venues together (for example, a \"best bars and "
        f"restaurants\" list), unless the excerpt is specifically and "
        f"substantially about a {primary_venue}."
    ).strip()


def build_search_queries(
    scene: Scene,
    requirements: LocationRequirements,
) -> list[str]:
    """
    Build diverse, keyword-style search queries for location discovery.

    Each query is kept close to Parallel's recommended 3-6 word range
    for keyword queries, and the list is capped at 5 (the API drops
    queries after the fifth).
    """

    region = compact_search_region(
        requirements.preferred_region
    )

    primary_venue, alternative_venue = (
        get_search_venue_terms(scene)
    )

    visual_terms = get_visual_search_terms(scene)

    queries: list[str] = []

    # ---------------------------------------------------------
    # 1. Basic venue discovery
    # ---------------------------------------------------------
    queries.append(
        f"{primary_venue} in {region}"
    )

    # ---------------------------------------------------------
    # 2. Alternative terminology
    # ---------------------------------------------------------
    if alternative_venue != primary_venue:
        queries.append(
            f"{alternative_venue} {region}"
        )

    # ---------------------------------------------------------
    # 3. Screenplay visual / architectural discovery
    # ---------------------------------------------------------
    if visual_terms:
        queries.append(
            f"{primary_venue} {visual_terms} {region}"
        )

    # ---------------------------------------------------------
    # 4. Production-specific search
    # ---------------------------------------------------------
    if requirements.location_type == "studio":
        queries.append(
            f"{primary_venue} film studio {region}"
        )

    elif requirements.location_type == "practical":
        queries.append(
            f"{primary_venue} rental {region}"
        )

    else:
        queries.append(
            f"{primary_venue} filming location {region}"
        )

    # ---------------------------------------------------------
    # 5. Practical details discovery (address, price, service style)
    # ---------------------------------------------------------
    queries.append(
        f"{primary_venue} menu reviews {region}"
    )

    return list(dict.fromkeys(queries))[:5]


def build_fallback_search_queries(
    scene: Scene,
    requirements: LocationRequirements,
) -> list[str]:
    """
    Build a single, maximally broad fallback query.

    Used when the primary, more specific queries from
    build_search_queries() return no usable results.
    """

    region = compact_search_region(
        requirements.preferred_region
    )

    primary_venue, _ = get_search_venue_terms(scene)

    return [f"{primary_venue} {region}"]


def execute_parallel_search(
    objective: str,
    search_queries: list[str],
    country_code: str | None = None,
) -> Any:
    """
    Execute the blocking Parallel SDK request.

    This function is run in a worker thread so the synchronous
    Parallel SDK does not block FastAPI's event loop.

    Retries up to MAX_SEARCH_ATTEMPTS times, with a backoff of
    RETRY_BACKOFF_SECONDS multiplied by the attempt number, to
    absorb transient network/API failures.

    country_code, when provided, biases results toward that country
    (see guess_country_code). Omitted entirely when None, rather than
    passed as an empty/guessed value.
    """

    api_key = os.getenv("PARALLEL_API_KEY")

    if not api_key:
        raise RuntimeError(
            "PARALLEL_API_KEY is missing."
        )

    client = Parallel(api_key=api_key)

    advanced_settings: dict[str, Any] = {
        "max_results": 8,
        "excerpt_settings": {
            "max_chars_per_result": 2000,
        },
        "source_policy": {
            "exclude_domains": LOW_QUALITY_DOMAINS,
        },
    }

    if country_code:
        advanced_settings["location"] = country_code

    last_error: Exception | None = None

    for attempt in range(1, MAX_SEARCH_ATTEMPTS + 1):
        try:
            return client.search(
                objective=objective,
                search_queries=search_queries,
                mode="advanced",
                client_model=LOCATION_AGENT_MODEL,
                max_chars_total=40_000,
                advanced_settings=advanced_settings,
            )

        except Exception as error:
            last_error = error

            if attempt < MAX_SEARCH_ATTEMPTS:
                logger.warning(
                    "Parallel search attempt %s/%s failed: %s",
                    attempt,
                    MAX_SEARCH_ATTEMPTS,
                    error,
                )

                time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise last_error


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

    all_excerpts = [
        excerpt
        for result in results
        for excerpt in result["excerpts"]
    ]

    average_excerpt_length = (
        round(
            sum(len(excerpt) for excerpt in all_excerpts)
            / len(all_excerpts)
        )
        if all_excerpts
        else 0
    )

    print("\n========== PARALLEL SEARCH ==========")
    print("\nSEARCH QUERIES")

    for index, query in enumerate(
        search_queries,
        start=1,
    ):
        print(f"{index}. {query}")

    print(
        f"\nUSABLE RESULTS: {len(results)} "
        f"(avg excerpt length: {average_excerpt_length} chars)"
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
                f"Excerpt {excerpt_index} "
                f"({len(excerpt)} chars): {excerpt}"
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

    country_code = guess_country_code(
        requirements.preferred_region
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
            country_code,
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

    if not results:
        logger.warning(
            "Primary location search returned no usable results; "
            "retrying with a broader fallback query."
        )

        fallback_queries = build_fallback_search_queries(
            scene=scene,
            requirements=requirements,
        )

        try:
            fallback_response = await asyncio.to_thread(
                execute_parallel_search,
                objective,
                fallback_queries,
                country_code,
            )

        except Exception as error:
            logger.exception(
                "Fallback parallel location search failed."
            )

            raise RuntimeError(
                f"Parallel location search failed: {error}"
            ) from error

        results = normalize_search_results(
            fallback_response
        )

        search_queries = fallback_queries

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