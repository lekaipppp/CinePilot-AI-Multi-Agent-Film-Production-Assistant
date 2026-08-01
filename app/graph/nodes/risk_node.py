"""
app/graph/nodes/risk_node.py
==============================
Risk Analysis node — pipeline step 5 (final content node).

Responsibilities (business logic to be implemented)
----------------------------------------------------
1. Receive the complete upstream state: scenes, locations, schedule,
   and budget from all previous nodes.
2. Call Gemini with a risk-analysis prompt that identifies production
   risks across six categories (weather, budget, schedule, legal,
   cast/crew, equipment) using the data accumulated by earlier nodes.
3. Score each risk (probability 1–5 × impact 1–5) and derive the
   overall risk level.
4. Return a structured risk report:
   ``state["risk_report"]`` — dict matching the ``RiskReport`` +
                               ``RiskItem`` ORM schema so it can be
                               written directly to the database.

Node contract
-------------
Reads  : ``scenes``, ``schedule``, ``budget_estimate``,
          ``location_results``, ``director_analysis``, ``run_metadata``
Writes : ``risk_report``
Errors : sets ``state["error"]`` on failure; does NOT raise

Current status
--------------
STUB — returns an empty risk report skeleton so the full pipeline can
       run end-to-end while the Gemini risk prompt is being written.
"""

from __future__ import annotations

from app.graph.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

NODE_NAME = "risk"


async def risk_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Risk Analyser.

    Reads  : ``scenes``, ``schedule``, ``budget_estimate``,
             ``location_results``, ``director_analysis``
    Writes : ``risk_report``
    """
    if state.get("error"):
        logger.info(
            "%s: skipping — upstream error is set",
            NODE_NAME,
            extra={"error": state["error"]},
        )
        return state

    scenes:          list = state.get("scenes", [])
    schedule:        dict = state.get("schedule", {})
    budget_estimate: dict = state.get("budget_estimate", {})
    location_results: list = state.get("location_results", [])

    logger.info(
        "%s: started",
        NODE_NAME,
        extra={
            "project_id":       state.get("project_id"),
            "scene_count":      len(scenes),
            "location_count":   len(location_results),
            "has_schedule":     bool(schedule.get("shoot_days")),
            "has_budget":       bool(budget_estimate.get("departments")),
        },
    )

    # ── TODO: implement AI risk analysis ──────────────────────────────────
    # Replace this stub with real logic:
    #
    #   gemini = GeminiService()
    #   prompt = RISK_PROMPT.format(
    #       scenes=json.dumps(scenes),
    #       schedule=json.dumps(schedule),
    #       budget=json.dumps(budget_estimate),
    #       locations=json.dumps(location_results),
    #   )
    #   raw = await gemini.generate_json(prompt)
    #   risk_report = RiskReportSchema(**raw)
    #
    risk_report: dict = {
        "overall_risk_level": "low",
        "summary":            "Risk analysis not yet generated.",
        "recommendations":    "",
        "items":              [],
    }

    logger.info(
        "%s: completed",
        NODE_NAME,
        extra={
            "project_id":         state.get("project_id"),
            "overall_risk_level": risk_report["overall_risk_level"],
            "risk_item_count":    len(risk_report["items"]),
        },
    )

    return {**state, "risk_report": risk_report}
