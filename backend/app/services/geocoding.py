import asyncio
import os
import time
from typing import Optional

import httpx

from backend.app.agents.location_agent import LocationAgentOutput
from backend.app.services.parallel_search import compact_search_region


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
MAPBOX_URL_TEMPLATE = (
    "https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
)

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

_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """
    Return a shared httpx client so repeated geocoding calls reuse
    the same connection pool instead of opening a new client per call.
    """

    global _http_client

    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=10.0)

    return _http_client


async def close_http_client() -> None:
    """
    Close the shared client. Call this from the FastAPI shutdown event.
    """

    global _http_client

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def parse_address_components(address: str) -> dict[str, str]:
    """
    Best-effort split of a US-style address into Nominatim's
    structured query fields.

    Example:
        "45 John St, New York, NY 10038, USA"
        -> {"street": "45 John St", "city": "New York",
            "state": "NY", "postalcode": "10038", "country": "USA"}
    """

    parts = [
        part.strip()
        for part in address.split(",")
        if part.strip()
    ]

    components: dict[str, str] = {}

    if not parts:
        return components

    components["street"] = parts[0]

    if len(parts) >= 2:
        components["city"] = parts[1]

    if len(parts) >= 3:
        state_zip = parts[2].split()

        if state_zip:
            components["state"] = state_zip[0]

        if len(state_zip) > 1:
            components["postalcode"] = state_zip[1]

    if len(parts) >= 4:
        components["country"] = parts[3]

    return components


async def geocode_query(
    query: str,
) -> Optional[tuple[float, float]]:
    """
    Convert a place name or address into latitude and longitude
    using Nominatim's free-text search.
    """

    global _last_request_time

    normalized_query = query.strip()

    if not normalized_query:
        return None

    cache_key = f"freetext:{normalized_query}"

    if cache_key in _geocoding_cache:
        return _geocoding_cache[cache_key]

    async with _rate_limit_lock:
        elapsed = time.monotonic() - _last_request_time

        if elapsed < 1:
            await asyncio.sleep(1 - elapsed)

        try:
            client = get_http_client()

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
            _geocoding_cache[cache_key] = None
            return None

    if not results:
        _geocoding_cache[cache_key] = None
        return None

    coordinates = (
        float(results[0]["lat"]),
        float(results[0]["lon"]),
    )

    _geocoding_cache[cache_key] = coordinates
    return coordinates


async def geocode_structured(
    address: str,
) -> Optional[tuple[float, float]]:
    """
    Convert an address into latitude and longitude using Nominatim's
    structured query fields (street/city/state/postalcode/country).

    This resolves real addresses far more reliably than a single
    free-text string, since Nominatim doesn't have to guess how to
    split the string into components.
    """

    global _last_request_time

    components = parse_address_components(address)

    if "street" not in components:
        return None

    cache_key = f"structured:{address.strip()}"

    if cache_key in _geocoding_cache:
        return _geocoding_cache[cache_key]

    async with _rate_limit_lock:
        elapsed = time.monotonic() - _last_request_time

        if elapsed < 1:
            await asyncio.sleep(1 - elapsed)

        try:
            client = get_http_client()

            response = await client.get(
                NOMINATIM_URL,
                params={
                    **components,
                    "format": "jsonv2",
                    "limit": 1,
                },
                headers=HEADERS,
            )

            _last_request_time = time.monotonic()
            response.raise_for_status()

            results = response.json()

        except (httpx.HTTPError, ValueError):
            _geocoding_cache[cache_key] = None
            return None

    if not results:
        _geocoding_cache[cache_key] = None
        return None

    coordinates = (
        float(results[0]["lat"]),
        float(results[0]["lon"]),
    )

    _geocoding_cache[cache_key] = coordinates
    return coordinates


async def geocode_with_mapbox(
    query: str,
) -> Optional[tuple[float, float]]:
    """
    Fallback geocoder used only when Nominatim fails to resolve a query.
    Requires MAPBOX_TOKEN to be set in the environment; silently skipped
    otherwise so the app still works with zero extra configuration.
    """

    token = os.getenv("MAPBOX_TOKEN")

    if not token:
        return None

    normalized_query = query.strip()

    if not normalized_query:
        return None

    cache_key = f"mapbox:{normalized_query}"

    if cache_key in _geocoding_cache:
        return _geocoding_cache[cache_key]

    encoded_query = normalized_query.replace(" ", "%20")
    url = MAPBOX_URL_TEMPLATE.format(query=encoded_query)

    try:
        client = get_http_client()

        response = await client.get(
            url,
            params={
                "access_token": token,
                "limit": 1,
            },
        )

        response.raise_for_status()
        data = response.json()

    except (httpx.HTTPError, ValueError):
        _geocoding_cache[cache_key] = None
        return None

    features = data.get("features") or []

    if not features:
        _geocoding_cache[cache_key] = None
        return None

    # Mapbox returns [longitude, latitude], reversed from Nominatim.
    longitude, latitude = features[0]["center"]
    coordinates = (latitude, longitude)

    _geocoding_cache[cache_key] = coordinates
    return coordinates


async def geocode_candidate(
    place_name: str,
    address: Optional[str],
    preferred_region: str,
) -> Optional[tuple[float, float]]:
    """
    Resolve coordinates for a location candidate.

    Order of attempts:
        1. Structured Nominatim query using the candidate's address.
        2. Free-text Nominatim query using the address alone.
        3. Free-text Nominatim query using the place name plus a
           compact version of the user's preferred region.
        4. Mapbox, only if Nominatim failed on every attempt above
           and MAPBOX_TOKEN is configured.
    """

    compact_region = compact_search_region(preferred_region)

    if address:
        coordinates = await geocode_structured(address)

        if coordinates is not None:
            return coordinates

    queries: list[str] = []

    if address:
        queries.append(address)

    queries.append(
        f"{place_name}, {compact_region}"
    )

    for query in dict.fromkeys(queries):
        coordinates = await geocode_query(query)

        if coordinates is not None:
            return coordinates

    fallback_query = (
        address
        if address
        else f"{place_name}, {compact_region}"
    )

    return await geocode_with_mapbox(fallback_query)


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