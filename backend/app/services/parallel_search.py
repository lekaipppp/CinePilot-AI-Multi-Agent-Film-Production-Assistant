import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from parallel import Parallel

from backend.app.agents.director_agent import Scene
from backend.app.schemas.location import LocationRequirements

load_dotenv()

def build_search_objective(
    scene: Scene,
    requirements: LocationRequirements,
) -> str:
    """
    Convert the Director scene analysis and user requirements into a
    detailed research objective for Parallel Search.
    """

    shooting_requirements = (
        ", ".join(scene.shooting_requirements)
        if scene.shooting_requirements
        else "No special shooting requirements specified"
    )

    additional_requirements = (
        requirements.additional_requirements
        if requirements.additional_requirements
        else "No additional user requirements"
    )

    filming_date = (
        requirements.filming_date.isoformat()
        if requirements.filming_date
        else "No filming date specified"
    )

    location_features = (
        ", ".join(scene.location_features)
        if scene.location_features
        else "No specific visual features identified"
    )
    
    return f"""
Find real, currently identifiable filming-location candidates for Scene
{scene.scene_number} near {requirements.preferred_region}.

Scene information:
- Scene heading: {scene.scene_heading}
- Fundamental venue type: {scene.location_setting or "Unspecified"}
- Required visual and architectural features: {location_features}
- Interior or exterior: {scene.interior_exterior}
- Time of day: {scene.time_of_day or "Unspecified"}
- Weather: {scene.weather_of_scene or "Unspecified"}
- Shooting requirements: {shooting_requirements}

User requirements:
- Preferred region: {requirements.preferred_region}
- Maximum distance: {requirements.maximum_distance_km} km
- Maximum day rate: {requirements.maximum_day_rate}
  {requirements.currency}
- Environment preference: {requirements.environment}
- Permit preference: {requirements.permit_preference}
- Location type: {requirements.location_type}
- Filming date: {filming_date}
- Additional requirements: {additional_requirements}

Search primarily for locations whose fundamental venue type matches the
scene. For example, when the scene requires a cafe, prioritize actual cafes,
restaurants with cafe-compatible interiors, cafe sets, or studios explicitly
advertising cafe sets.

Do not substitute houses, apartments, offices, or unrelated event spaces
merely because they accept film productions.

Prefer dedicated venue pages and individual rental listings over general
articles containing lists of loosely related properties.

Find up to 5 strong candidates. Returning fewer candidates is acceptable
when the evidence does not support enough suitable locations.

For every candidate, look for evidence of:
- correct venue type;
- required visual features;
- filming or rental permission;
- address or identifiable area;
- price or contact information;
- production amenities.

Do not invent missing information.
""".strip()

def build_search_queries(
    scene: Scene,
    requirements: LocationRequirements,
) -> list[str]:

    region = requirements.preferred_region.strip()

    setting = (
        scene.location_setting
        or scene.scene_heading
        or "filming location"
    ).strip()

    features = " ".join(scene.location_features[:3])

    production_type = {
        "practical": "real venue",
        "studio": "film studio set",
        "either": "filming location",
    }[requirements.location_type]

    queries = [
        (
            f'"{setting}" {features} '
            f'filming location rental "{region}"'
        ),
        (
            f'{production_type} "{setting}" '
            f'film production "{region}"'
        ),
        (
            f'"{setting}" photo shoot film rental '
            f'production venue "{region}"'
        ),
    ]

    if requirements.maximum_day_rate:
        queries.append(
            f'"{setting}" filming rental price "{region}"'
        )

    return [
        " ".join(query.split())
        for query in queries
    ]


def execute_parallel_search(
        objective: str,
        search_queries: list[str],
) -> Any:

    api_key = os.getenv("PARALLEL_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Parallel_API_KEY is missing."
        )

    client = Parallel(api_key=api_key)

    return client.search(
        objective=objective,
        search_queries=search_queries,
        mode="basic",
        max_chars_total=20_000,

    )


def normalize_search_results(search_response: Any) -> list[dict[str, Any]]:
    ''''
    Convert Parallel SDK result objects into ordinary dictionaries.

    These dictionaries can later be serilized as JSON, cuz we need to pass it to location agent
    '''

    normalized_results: list[dict[str, Any]] = []

    for result in search_response.results:
        normalized_results.append(
            {
                "title": result.title,
                "url": result.url,
                "excerpts": list(result.excerpts or []),
            }
        )

    return normalized_results



async def search_location_candidates(
        scene: Scene,
        requirements: LocationRequirements,
) -> list[dict[str, Any]]:

    '''Main function called by location.py

    It combines:
    1. Director Agent scene information
    2. User-entered location requirements
    '''

    objective = build_search_objective(scene=scene, requirements=requirements)

    search_queries = build_search_queries(scene=scene, requirements=requirements)

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

    results = normalize_search_results(search_response)

    if not results:
        raise RuntimeError(
            "Parallel Search returned no location candidates."
        )

    return results