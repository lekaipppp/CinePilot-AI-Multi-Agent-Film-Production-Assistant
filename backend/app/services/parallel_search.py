import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv
from parallel import Parallel

from backend.app.agents.director_agent import Scene
from backend.app.schemas.location import LocationRequirements


load_dotenv()

logger = logging.getLogger(__name__)


def build_search_objective(
    scene: Scene,
    requirements: LocationRequirements,
) -> str:
    """
    Convert the scene analysis and user requirements into a
    detailed research objective for Parallel Search.
    """

    shooting_requirements = (
        ", ".join(scene.shooting_requirements)
        if scene.shooting_requirements
        else "No special shooting requirements specified"
    )

    location_features = (
        ", ".join(scene.location_features)
        if scene.location_features
        else "No specific visual or architectural features identified"
    )

    additional_requirements = (
        requirements.additional_requirements.strip()
        if requirements.additional_requirements.strip()
        else "No additional user requirements"
    )

    filming_date = (
        requirements.filming_date.isoformat()
        if requirements.filming_date
        else "No filming date specified"
    )

    return f"""
Find real, currently identifiable filming-location candidates for Scene
{scene.scene_number} near {requirements.preferred_region}.

SCENE REQUIREMENTS

- Scene heading: {scene.scene_heading}
- Fundamental venue type: {scene.location_setting or "Unspecified"}
- Required visual and architectural features: {location_features}
- Interior or exterior: {scene.interior_exterior}
- Time of day: {scene.time_of_day or "Unspecified"}
- Weather visible or affecting the scene:
  {scene.weather_of_scene or "Unspecified"}
- Special shooting requirements: {shooting_requirements}

USER CONSTRAINTS

- Preferred filming region: {requirements.preferred_region}
- Maximum distance from region:
  {requirements.maximum_distance_km} km
- Maximum location day rate:
  {requirements.maximum_day_rate} {requirements.currency}
- Environment preference: {requirements.environment}
- Permit preference: {requirements.permit_preference}
- Required location type: {requirements.location_type}
- Preferred filming date: {filming_date}
- Additional requirements: {additional_requirements}

SEARCH PRIORITIES

Search primarily for locations whose fundamental venue type matches the
scene.

For example, if the scene requires a cafe, prioritize:

- actual cafes that publicly support filming or private rental;
- restaurants with cafe-compatible interiors;
- production venues with an identifiable cafe area;
- studios explicitly advertising a cafe set.

Do not substitute houses, apartments, offices, or unrelated event spaces
merely because they accept film productions.

A candidate located in the correct region is not automatically suitable.
Its documented appearance and venue type must also match the scene.

Prefer:

1. Dedicated pages for individual venues.
2. Individual film-location or production-rental listings.
3. Official venue websites containing filming, event, or contact details.
4. Reputable location directories and film-commission listings.

Avoid relying primarily on:

1. General articles listing loosely related properties.
2. Search-result pages without information about individual venues.
3. Travel articles that do not provide filming or rental evidence.
4. Unnamed or unidentifiable locations.

Find up to five strong candidates. Returning fewer candidates is acceptable
when sufficient evidence does not exist.

For each candidate, look for public evidence concerning:

- exact venue or property name;
- correct venue type;
- required visual or architectural features;
- address or identifiable area;
- filming, production, event, or private-rental permission;
- advertised price or contact-for-price information;
- production amenities;
- accessibility and load-in information;
- permit or availability information;
- an individual source URL.

Do not invent missing information. Missing details may remain unknown.
""".strip()


def build_search_queries(
    scene: Scene,
    requirements: LocationRequirements,
) -> list[str]:
    """
    Build three concise and diverse keyword queries.

    Detailed constraints belong in the objective. These queries help
    Parallel discover relevant categories of webpages.
    """

    region = requirements.preferred_region.strip()

    setting = (
        scene.location_setting
        or scene.scene_heading
        or "filming location"
    ).strip()

    if requirements.location_type == "studio":
        third_query = f"{setting} studio set {region}"

    elif requirements.location_type == "practical":
        third_query = f"{setting} real venue filming {region}"

    else:
        # Search the studio/set angle as an alternative to practical venues.
        third_query = f"{setting} film set {region}"

    return [
        f"{setting} filming rental {region}",
        f"{setting} production venue {region}",
        third_query,
    ]


def execute_parallel_search(
    objective: str,
    search_queries: list[str],
) -> Any:
    """
    Execute the blocking Parallel SDK request.

    This function is later run in a worker thread so that it does
    not block the FastAPI event loop.
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
    Convert Parallel SDK result objects into JSON-serializable
    dictionaries and remove duplicate source URLs.
    """

    normalized_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    search_results = getattr(
        search_response,
        "results",
        [],
    )

    for result in search_results:
        url = str(result.url).strip()

        if not url or url in seen_urls:
            continue

        excerpts = [
            str(excerpt).strip()
            for excerpt in (result.excerpts or [])
            if str(excerpt).strip()
        ]

        # Results without excerpts do not give the Location Agent
        # enough evidence to evaluate a candidate safely.
        if not excerpts:
            continue

        seen_urls.add(url)

        normalized_results.append(
            {
                "title": str(result.title).strip(),
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
    Log raw Parallel results for development and debugging.
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
        "Parallel returned %s source pages.",
        len(results),
    )

    for index, result in enumerate(results, start=1):
        logger.info(
            "Parallel result %s: %s | %s",
            index,
            result["title"],
            result["url"],
        )

        logger.debug(
            "Parallel result %s excerpts: %s",
            index,
            result["excerpts"],
        )


async def search_location_candidates(
    scene: Scene,
    requirements: LocationRequirements,
) -> list[dict[str, Any]]:
    """
    Search for real filming-location candidates using:

    1. Scene information from the Director Agent.
    2. Production constraints entered by the user.
    3. Current public webpages retrieved through Parallel.
    """

    objective = build_search_objective(
        scene=scene,
        requirements=requirements,
    )

    search_queries = build_search_queries(
        scene=scene,
        requirements=requirements,
    )

    try:
        search_response = await asyncio.to_thread(
            execute_parallel_search,
            objective,
            search_queries,
        )

    except Exception as error:
        raise RuntimeError(
            f"Parallel location search failed: {error}"
        ) from error

    results = normalize_search_results(
        search_response
    )

    if not results:
        raise RuntimeError(
            "Parallel Search returned no usable location sources."
        )

    log_search_results(
        objective=objective,
        search_queries=search_queries,
        results=results,
    )

    return results