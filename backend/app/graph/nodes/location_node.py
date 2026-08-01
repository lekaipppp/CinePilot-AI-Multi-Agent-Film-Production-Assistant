"""
app/graph/nodes/location_node.py
=================================
Location Scout node — pipeline step 2.

Responsibilities (business logic to be implemented)
----------------------------------------------------
1. Receive ``state["scenes"]`` from the Director node.
2. For every scene, call the Google Maps Geocoding API to resolve the
   ``location_query`` field into lat/lng coordinates.
3. Call the Google Places Nearby Search API to find the top candidate
   filming locations near those coordinates.
4. Call the OpenWeather API to fetch the current weather and 5-day
   forecast for each confirmed coordinate.
5. Write results to:
   ``state["location_results"]`` — list of location candidates per scene.
   ``state["weather_reports"]``  — weather data keyed by scene_number.

Node contract
-------------
Reads  : ``scenes``, ``run_metadata``
Writes : ``location_results``, ``weather_reports``
Errors : sets ``state["error"]`` on failure; does NOT raise

Current status
--------------
STUB — returns empty lists so the pipeline can run end-to-end while
       the Google Maps / OpenWeather integration is being built.
       Replace the body of ``_run()`` with the real implementation.
"""

from __future__ import annotations

from app.graph.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ── Node name used by the graph builder ──────────────────────────────────────
NODE_NAME = "location"


async def location_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Location Scout.

    Reads  : ``scenes``
    Writes : ``location_results``, ``weather_reports``
    """
    # ── Guard: skip if upstream already failed ────────────────────────────
    if state.get("error"):
        logger.info(
            "%s: skipping — upstream error is set",
            NODE_NAME,
            extra={"error": state["error"]},
        )
        return state

    scenes: list = state.get("scenes", [])

    logger.info(
        "%s: started",
        NODE_NAME,
        extra={
            "project_id": state.get("project_id"),
            "scene_count": len(scenes),
        },
    )

    # ── TODO: implement location scouting ─────────────────────────────────
    # Replace this stub with real logic:
    #
    #   location_service = LocationService()
    #   location_results = []
    #   weather_reports  = []
    #
    #   for scene in scenes:
    #       coords = await location_service.geocode(scene["location_query"])
    #       if coords:
    #           places  = await location_service.search_filming_locations(...)
    #           weather = await location_service.get_current_weather(...)
    #           forecast = await location_service.get_forecast(...)
    #           location_results.append({...})
    #           weather_reports.append({...})
    #
    location_results: list = []
    weather_reports:  list = []

    logger.info(
        "%s: completed",
        NODE_NAME,
        extra={
            "project_id":       state.get("project_id"),
            "locations_found":  len(location_results),
            "weather_reports":  len(weather_reports),
        },
    )

    return {
        **state,
        "location_results": location_results,
        "weather_reports":  weather_reports,
    }
