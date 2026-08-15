import asyncio
import time
from typing import Optional

import httpx

from backend.app.agents.location_agent import LocationAgentOutput


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": (
        "CinePilot/1.0 "
        "(https://github.com/lekaipppp/"
        "CinePilot-AI-Multi-Agent-Film-Production-Assistant)"
    )
}

_rate_limit_lock = asyncio.Lock()
_last_request_time = 0.0

_geocoding_cache: dict[
    str,
    Optional[tuple[float, float]],
] = {}


async def geocode_query(
    query: str,
) -> Optional[tuple[float, float]]:
    """
    Convert a place name or address into latitude and longitude.
    """

    global _last_request_time

    normalized_query = query.strip()

    if not normalized_query:
        return None

    if normalized_query in _geocoding_cache:
        return _geocoding_cache[normalized_query]

    async with _rate_limit_lock:
        elapsed = time.monotonic() - _last_request_time

        if elapsed < 1:
            await asyncio.sleep(1 - elapsed)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    NOMINATIM_URL,
                    params={
                        "q": normalized_query,
                        "format": "jsonv2",
                        "limit": 1,
                    },
                    headers=HEADERS,
                )

                _last_request_time = time.monotonic()
                response.raise_for_status()

                results = response.json()

        except (httpx.HTTPError, ValueError):
            _geocoding_cache[normalized_query] = None
            return None

    if not results:
        _geocoding_cache[normalized_query] = None
        return None

    coordinates = (
        float(results[0]["lat"]),
        float(results[0]["lon"]),
    )

    _geocoding_cache[normalized_query] = coordinates
    return coordinates


async def geocode_candidate(
    place_name: str,
    address: Optional[str],
    preferred_region: str,
) -> Optional[tuple[float, float]]:
    """
    Try the candidate address first, then fall back to its name.
    """

    queries: list[str] = []

    if address:
        queries.append(
            f"{address}, {preferred_region}"
        )

    queries.append(
        f"{place_name}, {preferred_region}"
    )

    for query in dict.fromkeys(queries):
        coordinates = await geocode_query(query)

        if coordinates is not None:
            return coordinates

    return None


async def add_coordinates_to_locations(
    location_result: LocationAgentOutput,
    preferred_region: str,
) -> LocationAgentOutput:
    """
    Add verified coordinates to every candidate returned by
    the Location Agent.
    """

    for recommendation in (
        location_result.scene_recommendations
    ):
        for candidate in recommendation.candidates:
            if (
                candidate.latitude is not None
                and candidate.longitude is not None
            ):
                continue

            coordinates = await geocode_candidate(
                place_name=candidate.place_name,
                address=candidate.address,
                preferred_region=preferred_region,
            )

            if coordinates is None:
                continue

            candidate.latitude = coordinates[0]
            candidate.longitude = coordinates[1]

    return location_result