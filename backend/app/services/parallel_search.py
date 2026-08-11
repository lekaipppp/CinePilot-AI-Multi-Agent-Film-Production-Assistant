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

    return f"""
Find real, currently identifiable filming-location candidates for Scene
{scene.scene_number} near {requirements.preferred_region}.

Scene information:
- Scene heading: {scene.scene_heading}
- Required setting: {scene.location_setting or "Unspecified"}
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

Prioritize real venues, properties, studios, tourism or film-commission
listings, and location directories. Look for evidence concerning the
location's appearance, address, filming suitability, rental information,
permit information, accessibility, and contact details. Do not invent
prices or availability when a source does not provide them.
""".strip()


def build_search_queries(
        scene: Scene,
        requirements: LocationRequirements,
) -> list[str]:

    region = requirements.preferred_region

    setting = (
        scene.location_setting
        or scene.scene_heading
        or "filmiong location"
    )

    return [
        f"{setting} filming location {region}",
        f"film locations {region} rental",
        f"{requirements.location_type} film venue {region}",
    ]


def execute_parallel_search(
        objective: str,
        search_quries: list[str],
) -> Any:

    api_key = os.getenv("PARALLEL_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Parallel_API)KEY is missing."
        )

    client = Parallel(api_key=api_key)

    return client.search(
        objective=objective,
        search_quries=search_quries,
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

    search_queries = build_search_objective(scene=scene, requirements=requirements)

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