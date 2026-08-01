"""
SchedulerAgent – LangGraph node.
Proposes an optimised shooting schedule using Gemini,
informed by scenes, locations, and weather data.
"""

import json

from app.graph.state import AgentState
from app.services.gemini_service import GeminiService

_gemini = GeminiService()

SCHEDULER_PROMPT = """
You are an experienced film production manager.
Using the scene breakdown and weather/location data below, produce a realistic
shooting schedule that minimises location travel and avoids poor weather.

Scene Breakdown:
{scenes}

Location & Weather Data:
{weather_reports}

Return a JSON object with:
  - shoot_days (array of objects, each with: date, scenes (array of scene_numbers), location, notes)
  - total_shoot_days (int)
  - scheduling_notes (string)
""".strip()


async def scheduler_node(state: AgentState) -> AgentState:
    """
    LangGraph node: generate a shooting schedule.
    Reads `scenes` + `weather_reports`, writes `schedule`.
    """
    scenes = state.get("scenes", [])
    weather_reports = state.get("weather_reports", [])

    prompt = SCHEDULER_PROMPT.format(
        scenes=json.dumps(scenes, indent=2),
        weather_reports=json.dumps(weather_reports, indent=2),
    )

    try:
        schedule = await _gemini.generate_json(prompt)
        return {**state, "schedule": schedule}
    except Exception as exc:
        return {**state, "error": f"SchedulerAgent failed: {exc}"}
