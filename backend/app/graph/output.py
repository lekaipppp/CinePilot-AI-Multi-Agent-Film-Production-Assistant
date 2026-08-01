"""
app/graph/output.py
====================
Production Plan assembler — the final node in the CinePilot pipeline.

Responsibility
--------------
Collect every piece of data written by the five upstream nodes and
assemble it into a single ``production_plan`` dict that:

1. Can be JSON-serialised and returned as the HTTP response body.
2. Can be stored as-is in the ``agent_sessions.state_snapshot`` JSONB column.
3. Contains enough metadata (timestamps, node versions, error info) for
   debugging and auditing.

Why a dedicated node?
---------------------
Assembling the plan inside the API router (or service layer) would couple
the graph's internal state shape to the HTTP contract.  A dedicated node
keeps that contract inside the graph module and lets the router stay thin:

    result = await cinepilot_graph.ainvoke(state)
    return result["production_plan"]   # ← one key, always present

The ``assemble_output`` node is **always** the last node in the graph,
including on the error path — the error handler routes here too, so
``production_plan`` is always written even when the pipeline failed.

``production_plan`` shape
-------------------------
{
    "project_id":         str | None,
    "status":             "complete" | "partial" | "failed",
    "error":              str | None,
    "title":              str | None,    # from director_analysis
    "genre":              str | None,
    "logline":            str | None,
    "scene_count":        int,
    "scenes":             list[dict],
    "characters":         list[dict],
    "props":              list[dict],
    "locations":          list[dict],
    "shooting_requirements": dict,
    "location_results":   list[dict],
    "weather_reports":    list[dict],
    "schedule":           dict,
    "budget_estimate":    dict,
    "risk_report":        dict,
    "run_metadata":       dict,
}
"""

from __future__ import annotations

import time
from typing import Any

from app.graph.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

NODE_NAME = "assemble_output"


def _determine_status(state: AgentState) -> str:
    """
    Derive a pipeline status string from the final state.

    ``"complete"``  — no error, all five content keys are present.
    ``"partial"``   — no error, but one or more content keys are missing
                      (e.g. location scouting returned nothing).
    ``"failed"``    — ``state["error"]`` is set.
    """
    if state.get("error"):
        return "failed"

    required_keys = (
        "director_analysis",
        "location_results",
        "schedule",
        "budget_estimate",
        "risk_report",
    )
    all_present = all(state.get(k) for k in required_keys)
    return "complete" if all_present else "partial"


async def assemble_output_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Production Plan assembler.

    Always runs — including on the error path.

    Reads  : all pipeline keys
    Writes : ``production_plan``
    """
    status = _determine_status(state)

    director: dict[str, Any] = state.get("director_analysis") or {}

    production_plan: dict[str, Any] = {
        # ── Identity ───────────────────────────────────────────────────
        "project_id": state.get("project_id"),
        "status":     status,
        "error":      state.get("error"),

        # ── Director output ────────────────────────────────────────────
        "title":                 director.get("title"),
        "genre":                 director.get("genre"),
        "logline":               director.get("logline"),
        "scene_count":           len(state.get("scenes") or []),
        "scenes":                state.get("scenes") or [],
        "characters":            director.get("characters") or [],
        "props":                 director.get("props") or [],
        "locations":             director.get("locations") or [],
        "shooting_requirements": director.get("shooting_requirements") or {},

        # ── Location output ────────────────────────────────────────────
        "location_results": state.get("location_results") or [],
        "weather_reports":  state.get("weather_reports") or [],

        # ── Scheduler output ───────────────────────────────────────────
        "schedule":         state.get("schedule") or {},

        # ── Budget output ──────────────────────────────────────────────
        "budget_estimate":  state.get("budget_estimate") or {},

        # ── Risk output ────────────────────────────────────────────────
        "risk_report":      state.get("risk_report") or {},

        # ── Run metadata ───────────────────────────────────────────────
        "run_metadata": {
            **(state.get("run_metadata") or {}),
            "assembled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pipeline_status": status,
        },
    }

    logger.info(
        "%s: production plan assembled",
        NODE_NAME,
        extra={
            "project_id":  state.get("project_id"),
            "status":      status,
            "scene_count": production_plan["scene_count"],
        },
    )

    return {**state, "production_plan": production_plan}
