"""
LocationScoutAgent – LangGraph node.
Uses Google Maps / Places to find real-world filming locations for each scene.
"""

from app.graph.state import AgentState
from app.services.location_service import LocationService

_location = LocationService()


async def location_scout_node(state: AgentState) -> AgentState:
    """
    LangGraph node: geocode + nearby-search for every scene's location_query.
    Reads `scenes`, writes `location_results`.
    """
    scenes = state.get("scenes", [])
    if not scenes:
        return {**state, "location_results": []}

    results = []
    for scene in scenes:
        query = scene.get("location_query", "")
        coords = await _location.geocode(query)
        if coords:
            places = await _location.search_filming_locations(
                query=query,
                lat=coords["lat"],
                lng=coords["lng"],
            )
            results.append(
                {
                    "scene_number": scene.get("scene_number"),
                    "query": query,
                    "coordinates": coords,
                    "places": places[:5],  # top 5 candidates per scene
                }
            )
        else:
            results.append(
                {
                    "scene_number": scene.get("scene_number"),
                    "query": query,
                    "coordinates": None,
                    "places": [],
                }
            )

    return {**state, "location_results": results}
