"""
WeatherAgent – LangGraph node.
Fetches current weather and 5-day forecasts for each scouted location.
"""

from app.graph.state import AgentState
from app.services.location_service import LocationService

_location = LocationService()


async def weather_node(state: AgentState) -> AgentState:
    """
    LangGraph node: enrich location results with weather data.
    Reads `location_results`, writes `weather_reports`.
    """
    location_results = state.get("location_results", [])
    reports = []

    for loc in location_results:
        coords = loc.get("coordinates")
        if not coords:
            reports.append(
                {"scene_number": loc["scene_number"], "weather": None, "forecast": None}
            )
            continue

        weather = await _location.get_current_weather(coords["lat"], coords["lng"])
        forecast = await _location.get_forecast(coords["lat"], coords["lng"])

        reports.append(
            {
                "scene_number": loc["scene_number"],
                "coordinates": coords,
                "weather": weather,
                "forecast": forecast,
            }
        )

    return {**state, "weather_reports": reports}
