"""
SceneBreakdownAgent – LangGraph node.
Parses the script draft into a structured list of scenes.
"""

from app.graph.state import AgentState
from app.services.gemini_service import GeminiService

_gemini = GeminiService()

BREAKDOWN_PROMPT = """
You are a professional script supervisor.
Given the following film script, extract a structured JSON scene breakdown.

Script:
{script}

Return a JSON array where each element has:
  - scene_number (int)
  - title (string)
  - description (string)
  - location_query (string – what to search for in Google Maps)
  - int_ext (string – "INT" or "EXT")
  - time_of_day (string – "DAY", "NIGHT", "DUSK", "DAWN")
""".strip()


async def scene_breakdown_node(state: AgentState) -> AgentState:
    """
    LangGraph node: decompose the script draft into individual scenes.
    Reads `script_draft`, writes `scenes`.
    """
    script = state.get("script_draft", "")
    if not script:
        return {**state, "error": "scene_breakdown: no script_draft in state."}

    prompt = BREAKDOWN_PROMPT.format(script=script)

    try:
        scenes = await _gemini.generate_json(prompt)
        return {**state, "scenes": scenes}
    except Exception as exc:
        return {**state, "error": f"SceneBreakdownAgent failed: {exc}"}
