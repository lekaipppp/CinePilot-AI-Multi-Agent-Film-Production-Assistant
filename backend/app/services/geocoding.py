#The backend connects to the OpenStreetMap data service(Nomination)
import asyncio
from typing import Optional
import time
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

#This is the global variable that holds the timestamp of the exact moment the last sucessful request was made.
_last_request_time = 0.0 

_geocoding_cache: dict[
    str, 
    Optional[tuple[float, float]],
    ] = {}


async def geocode_query(
        query: str,
) -> Optional[tuple[float, float]]:

    #convert a place name or address into latitude and longitude

    global _last_request_time #global is a keyword that tells a functin it is allowed to modify a variable that loves outside of that function

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
'''with is called a context manager.
Its only job in the entire language is to 
guarantee the cleanup code runs, no matter what happens.
'''
            
            async with 


