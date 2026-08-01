"""
app/graph/state.py
==================
LangGraph state definition — the shared TypedDict that flows through
every node in the CinePilot multi-agent graph.

Convention
----------
* All keys are ``total=False`` (optional) so nodes can be added or removed
  from the pipeline without breaking nodes that do not touch those keys.
* Each node reads from a documented set of keys and writes to a documented
  set of keys — see the table below.
* Never add mutable default values here — TypedDict is not a dataclass.
* The final assembled result lives in ``production_plan``; it is the only
  key the API response layer reads.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    Mutable state bag passed between LangGraph nodes.

    Key                  Written by            Read by
    ───────────────────  ────────────────────  ────────────────────────────────────
    project_id           API / router          all nodes (context)
    agent_type           API / router          all nodes (context)
    input_data           API / router          director_node
    messages             any node              all nodes
    error                any node on failure   all nodes (guard clause)
    run_metadata         graph runner          output assembler

    script_draft         script_writer_node    director_node
    director_analysis    director_node         location_node, output
    scenes               director_node         location_node, scheduler_node,
                                               budget_node, risk_node, output
    location_results     location_node         scheduler_node, risk_node, output
    weather_reports      location_node         scheduler_node, output
    schedule             scheduler_node        budget_node, risk_node, output
    budget_estimate      budget_node           risk_node, output
    risk_report          risk_node             output
    production_plan      output assembler      API response layer
    """

    # ── Execution context ──────────────────────────────────────────────────
    project_id:   str
    agent_type:   str
    input_data:   Dict[str, Any]
    messages:     List[Any]
    error:        Optional[str]

    # Timing and provenance written by the runner before graph invocation
    # so every node can emit it in structured logs.
    run_metadata: Dict[str, Any]

    # ── Pipeline data (in execution order) ────────────────────────────────
    script_draft:      str
    director_analysis: Dict[str, Any]   # DirectorAnalysis.model_dump()
    scenes:            List[Dict[str, Any]]

    location_results:  List[Dict[str, Any]]
    weather_reports:   List[Dict[str, Any]]

    schedule:          Dict[str, Any]
    budget_estimate:   Dict[str, Any]
    risk_report:       Dict[str, Any]   # written by risk_node

    # ── Final assembled output ────────────────────────────────────────────
    production_plan:   Dict[str, Any]   # written by output assembler node
