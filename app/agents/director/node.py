"""
app/agents/director/node.py
============================
LangGraph node function for the Director Agent.

Architecture rule
-----------------
This module contains **exactly one function**: ``director_node``.
It is the bridge between the LangGraph state machine and the
``DirectorAgent`` class — translating between the flat ``AgentState``
TypedDict and the typed ``DirectorAgentInput`` / ``DirectorAnalysis`` schemas.

Node contract
-------------
Reads from state:
    ``script_draft``  — screenplay text produced by ``script_writer_node``.
    ``input_data``    — raw user payload (checked for optional overrides:
                        ``max_scenes``, ``temperature``).

Writes to state:
    ``director_analysis``  — ``DirectorAnalysis.model_dump()`` dict.
    ``scenes``             — list of scene dicts (compatible with
                             downstream ``scene_breakdown_node`` and DB write).
    ``error``              — set on failure; downstream nodes should check
                             this and short-circuit if present.

Error handling
--------------
On ``AgentExecutionError``: sets ``state["error"]`` and returns the state
unchanged (except for the error field).  This follows the LangGraph
convention for soft failures — the graph continues to END without
crashing the orchestrator.
"""

from __future__ import annotations

from app.agents.director.agent import director_agent
from app.agents.director.schemas import DirectorAgentInput
from app.exceptions import AgentExecutionError
from app.graph.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def director_node(state: AgentState) -> AgentState:
    """
    LangGraph node: analyse the screenplay draft with the Director Agent.

    Reads  : ``script_draft``, ``input_data``
    Writes : ``director_analysis``, ``scenes``, (``error`` on failure)
    """
    # ── Guard: require a script draft ────────────────────────────────────
    screenplay = state.get("script_draft", "").strip()
    if not screenplay:
        error_msg = "director_node: 'script_draft' is empty — cannot run analysis."
        logger.warning(error_msg)
        return {**state, "error": error_msg}

    # ── Guard: skip if a previous node already set an error ──────────────
    if state.get("error"):
        logger.info(
            "director_node: skipping because upstream error is set",
            extra={"error": state["error"]},
        )
        return state

    # ── Extract optional overrides from input_data ────────────────────────
    input_data_raw = state.get("input_data", {})
    agent_input = DirectorAgentInput(
        screenplay=screenplay,
        max_scenes=input_data_raw.get("max_scenes"),
        temperature=float(input_data_raw.get("temperature", 0.1)),
    )

    # ── Run analysis ──────────────────────────────────────────────────────
    try:
        analysis = await director_agent.analyse(agent_input)
    except AgentExecutionError as exc:
        error_msg = f"director_node failed: {exc}"
        logger.error(error_msg)
        return {**state, "error": error_msg}

    # ── Serialise to plain dicts for JSONB / downstream nodes ─────────────
    analysis_dict = analysis.model_dump()

    # ``scenes`` in AgentState is the canonical scene list shared by all
    # downstream nodes (location scout, scheduler, etc.).  We populate it
    # from the Director's richer scene analysis to avoid re-running a
    # separate scene-breakdown call.
    scenes_for_state = [
        {
            "scene_number":   s.scene_number,
            "slug_line":      s.slug_line,
            "title":          s.slug_line,          # downstream compat alias
            "description":    s.description,
            "location_name":  s.location_name,
            "location_query": s.location_query,
            "int_ext":        s.int_ext,
            "time_of_day":    s.time_of_day,
            "characters":     s.characters,
            "props":          s.props,
            "shooting_notes": s.shooting_notes,
            "page_count":     s.page_count,
        }
        for s in analysis.scenes
    ]

    logger.info(
        "director_node completed",
        extra={
            "project_id":      state.get("project_id"),
            "scene_count":     analysis.scene_count,
            "character_count": len(analysis.characters),
        },
    )

    return {
        **state,
        "director_analysis": analysis_dict,
        "scenes":            scenes_for_state,
    }
