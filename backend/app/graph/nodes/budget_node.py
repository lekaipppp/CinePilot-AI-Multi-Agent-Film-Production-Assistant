"""
app/graph/nodes/budget_node.py
================================
Budget node — pipeline step 4.

Responsibilities (business logic to be implemented)
----------------------------------------------------
1. Receive ``state["scenes"]``, ``state["schedule"]``, and
   ``state["location_results"]`` from upstream nodes.
2. Call Gemini with a budget prompt that produces per-department cost
   estimates informed by the shoot duration, locations, and scene
   complexity (VFX, stunts, special equipment flagged by the Director).
3. Return a structured budget:
   ``state["budget_estimate"]`` — dict with currency, departments,
                                   total_estimated_cost, contingency_pct,
                                   assumptions.

Node contract
-------------
Reads  : ``scenes``, ``schedule``, ``director_analysis``, ``run_metadata``
Writes : ``budget_estimate``
Errors : sets ``state["error"]`` on failure; does NOT raise

Current status
--------------
STUB — returns an empty budget skeleton so the pipeline can run
       end-to-end while the Gemini budget prompt is being written.
"""

from __future__ import annotations

from app.graph.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

NODE_NAME = "budget"


async def budget_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Budget Estimator.

    Reads  : ``scenes``, ``schedule``, ``director_analysis``
    Writes : ``budget_estimate``
    """
    if state.get("error"):
        logger.info(
            "%s: skipping — upstream error is set",
            NODE_NAME,
            extra={"error": state["error"]},
        )
        return state

    scenes:   list = state.get("scenes", [])
    schedule: dict = state.get("schedule", {})

    logger.info(
        "%s: started",
        NODE_NAME,
        extra={
            "project_id":      state.get("project_id"),
            "scene_count":     len(scenes),
            "shoot_days":      schedule.get("total_shoot_days", 0),
        },
    )

    # ── TODO: implement AI budgeting ───────────────────────────────────────
    # Replace this stub with real logic:
    #
    #   gemini = GeminiService()
    #   prompt = BUDGET_PROMPT.format(
    #       schedule=json.dumps(schedule),
    #       scenes=json.dumps(scenes),
    #   )
    #   budget = await gemini.generate_json(prompt)
    #
    budget_estimate: dict = {
        "currency":             "USD",
        "departments":          [],
        "total_estimated_cost": 0,
        "contingency_pct":      10.0,
        "assumptions":          "Budget not yet generated.",
    }

    logger.info(
        "%s: completed",
        NODE_NAME,
        extra={
            "project_id":           state.get("project_id"),
            "total_estimated_cost": budget_estimate["total_estimated_cost"],
        },
    )

    return {**state, "budget_estimate": budget_estimate}
