"""
app/graph/nodes/scheduler_node.py
==================================
Scheduler node — pipeline step 3.

Responsibilities (business logic to be implemented)
----------------------------------------------------
1. Receive ``state["scenes"]``, ``state["location_results"]``, and
   ``state["weather_reports"]`` from the Location node.
2. Call Gemini with a scheduling prompt that groups scenes by location,
   avoids bad-weather days, and minimises crew travel.
3. Return a structured shooting schedule:
   ``state["schedule"]`` — dict with shoot_days, total_shoot_days,
                            scheduling_notes.

Node contract
-------------
Reads  : ``scenes``, ``location_results``, ``weather_reports``, ``run_metadata``
Writes : ``schedule``
Errors : sets ``state["error"]`` on failure; does NOT raise

Current status
--------------
STUB — returns an empty schedule skeleton so the pipeline can run
       end-to-end while the Gemini scheduling prompt is being written.
       Replace the body of ``_run()`` with the real implementation.
"""

from __future__ import annotations

from app.graph.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

NODE_NAME = "scheduler"


async def scheduler_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Shooting Scheduler.

    Reads  : ``scenes``, ``location_results``, ``weather_reports``
    Writes : ``schedule``
    """
    if state.get("error"):
        logger.info(
            "%s: skipping — upstream error is set",
            NODE_NAME,
            extra={"error": state["error"]},
        )
        return state

    scenes:           list = state.get("scenes", [])
    location_results: list = state.get("location_results", [])
    weather_reports:  list = state.get("weather_reports", [])

    logger.info(
        "%s: started",
        NODE_NAME,
        extra={
            "project_id":        state.get("project_id"),
            "scene_count":       len(scenes),
            "location_count":    len(location_results),
            "weather_available": len(weather_reports) > 0,
        },
    )

    # ── TODO: implement AI scheduling ─────────────────────────────────────
    # Replace this stub with real logic:
    #
    #   gemini = GeminiService()
    #   prompt = SCHEDULER_PROMPT.format(
    #       scenes=json.dumps(scenes),
    #       weather_reports=json.dumps(weather_reports),
    #   )
    #   schedule = await gemini.generate_json(prompt)
    #
    schedule: dict = {
        "shoot_days":        [],
        "total_shoot_days":  0,
        "scheduling_notes":  "Schedule not yet generated.",
    }

    logger.info(
        "%s: completed",
        NODE_NAME,
        extra={
            "project_id":      state.get("project_id"),
            "total_shoot_days": schedule["total_shoot_days"],
        },
    )

    return {**state, "schedule": schedule}
