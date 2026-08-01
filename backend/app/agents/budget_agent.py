"""
BudgetAgent – LangGraph node.
Produces a high-level budget estimate using Gemini,
based on the approved schedule and scene data.
"""

import json

from app.graph.state import AgentState
from app.services.gemini_service import GeminiService

_gemini = GeminiService()

BUDGET_PROMPT = """
You are a film production accountant.
Based on the shooting schedule and scene details below, generate a high-level
budget estimate broken down by department.

Shooting Schedule:
{schedule}

Scene Breakdown:
{scenes}

Return a JSON object with:
  - currency (string, e.g. "USD")
  - departments (array of objects: name, estimated_cost)
  - total_estimated_cost (number)
  - assumptions (string)
""".strip()


async def budget_node(state: AgentState) -> AgentState:
    """
    LangGraph node: generate a high-level budget estimate.
    Reads `schedule` + `scenes`, writes `budget_estimate`.
    """
    schedule = state.get("schedule", {})
    scenes = state.get("scenes", [])

    prompt = BUDGET_PROMPT.format(
        schedule=json.dumps(schedule, indent=2),
        scenes=json.dumps(scenes, indent=2),
    )

    try:
        budget = await _gemini.generate_json(prompt)
        return {**state, "budget_estimate": budget}
    except Exception as exc:
        return {**state, "error": f"BudgetAgent failed: {exc}"}
