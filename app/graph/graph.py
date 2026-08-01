"""
app/graph/graph.py
==================
LangGraph workflow builder for CinePilot AI.

Lazy initialisation: ``cinepilot_graph`` and ``workflow_runner`` are built on
first access, NOT at module import time.  This means:
- Importing ``app.graph`` never crashes at startup.
- LangGraph is only required when the pipeline is actually triggered.
- Tests can import the graph module without having LangGraph installed.

Pipeline topology
-----------------

  START
    │
    ▼
 ┌──────────┐   error   ┌────────────────┐
 │ director │──────────►│ error_handler  │
 └────┬─────┘           └───────┬────────┘
      │ ok                      │ (always)
      ▼                         │
 ┌──────────┐   error           │
 │ location │──────────►────────┤
 └────┬─────┘                   │
      │ ok                      │
      ▼                         │
 ┌───────────┐  error            │
 │ scheduler │─────────►─────────┤
 └─────┬─────┘                   │
       │ ok                      │
       ▼                         │
 ┌────────┐    error             │
 │ budget │────────────►─────────┤
 └───┬────┘                      │
     │ ok                        │
     ▼                           │
 ┌──────┐      error             │
 │ risk │──────────────►─────────┤
 └──┬───┘                        │
   │ ok                         │
   └──────────────────►─────────►
                                │
                                ▼
                       ┌────────────────┐
                       │ assemble_output│
                       └───────┬────────┘
                               │
                               ▼
                             END
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.config.settings import settings
from app.exceptions import AgentExecutionError
from app.graph.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Error handler node (no external deps — always importable)
# ---------------------------------------------------------------------------

async def error_handler_node(state: AgentState) -> AgentState:
    """
    Lightweight pass-through that logs a pipeline failure.
    Routes unconditionally to ``assemble_output`` so the final plan is
    always written — even when the pipeline failed.
    """
    logger.error(
        "Pipeline error — routing to output assembler",
        extra={
            "project_id": state.get("project_id"),
            "error":      state.get("error"),
        },
    )
    return state


# ---------------------------------------------------------------------------
# Graph builder — imports LangGraph only when called
# ---------------------------------------------------------------------------

def build_graph():
    """
    Construct and compile the CinePilot LangGraph workflow.

    LangGraph is imported **inside** this function so that importing the
    ``app.graph`` package never requires LangGraph to be present.

    Returns
    -------
    Compiled StateGraph
        Ready to be invoked with ``await graph.ainvoke(initial_state)``.

    Raises
    ------
    ImportError
        When ``langgraph`` is not installed.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise ImportError(
            "langgraph is not installed. "
            "Run: pip install langgraph"
        ) from exc

    # Import nodes only when building — they pull in google-generativeai etc.
    from app.graph.edges import (
        ERROR_HANDLER,
        route_after_budget,
        route_after_director,
        route_after_location,
        route_after_risk,
        route_after_scheduler,
    )
    from app.graph.nodes import (
        budget_node,
        director_node,
        location_node,
        risk_node,
        scheduler_node,
    )
    from app.graph.output import assemble_output_node

    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────
    graph.add_node("director",        director_node)
    graph.add_node("location",        location_node)
    graph.add_node("scheduler",       scheduler_node)
    graph.add_node("budget",          budget_node)
    graph.add_node("risk",            risk_node)
    graph.add_node("error_handler",   error_handler_node)
    graph.add_node("assemble_output", assemble_output_node)

    # ── Entry point ───────────────────────────────────────────────────────
    graph.add_edge(START, "director")

    # ── Conditional edges ─────────────────────────────────────────────────
    graph.add_conditional_edges(
        "director",
        route_after_director,
        {"location": "location", ERROR_HANDLER: "error_handler"},
    )
    graph.add_conditional_edges(
        "location",
        route_after_location,
        {"scheduler": "scheduler", ERROR_HANDLER: "error_handler"},
    )
    graph.add_conditional_edges(
        "scheduler",
        route_after_scheduler,
        {"budget": "budget", ERROR_HANDLER: "error_handler"},
    )
    graph.add_conditional_edges(
        "budget",
        route_after_budget,
        {"risk": "risk", ERROR_HANDLER: "error_handler"},
    )
    graph.add_conditional_edges(
        "risk",
        route_after_risk,
        {"assemble_output": "assemble_output", ERROR_HANDLER: "error_handler"},
    )

    # ── Error handler always flows to output assembler ────────────────────
    graph.add_edge("error_handler", "assemble_output")

    # ── Output assembler is always the terminal node ──────────────────────
    graph.add_edge("assemble_output", END)

    recursion_limit = getattr(settings, "LANGGRAPH_RECURSION_LIMIT", 50)

    return graph.compile(recursion_limit=recursion_limit)


# ---------------------------------------------------------------------------
# Lazy singletons — built on first access
# ---------------------------------------------------------------------------

_cinepilot_graph = None
_workflow_runner = None


def _get_graph():
    """Return (or lazily build) the compiled graph singleton."""
    global _cinepilot_graph
    if _cinepilot_graph is None:
        _cinepilot_graph = build_graph()
    return _cinepilot_graph


class WorkflowRunner:
    """
    Thin async facade over the compiled LangGraph workflow.

    The graph is built on the first call to ``run()`` — not at instantiation.
    Inject a pre-built graph in tests::

        runner = WorkflowRunner(graph=mock_graph)
    """

    def __init__(self, graph=None) -> None:
        # Accept an injected graph for testing; otherwise use the lazy singleton
        self._graph_override = graph

    def _get_graph(self):
        """Return the graph — either injected or the lazy singleton."""
        if self._graph_override is not None:
            return self._graph_override
        return _get_graph()

    async def run(
        self,
        *,
        project_id: str,
        screenplay: str,
        input_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute the full 5-node production planning pipeline.

        Parameters
        ----------
        project_id:
            UUID string of the project being processed.
        screenplay:
            Full screenplay text passed to the Director node.
        input_data:
            Optional per-run overrides (e.g. ``{"temperature": 0.1}``).

        Returns
        -------
        dict
            The ``production_plan`` dict assembled by ``assemble_output_node``.

        Raises
        ------
        AgentExecutionError
            Wraps any unhandled exception from the LangGraph runtime.
        """
        run_id  = str(uuid.uuid4())
        started = time.time()

        initial_state: AgentState = {
            "project_id":   project_id,
            "agent_type":   "production_planning",
            "script_draft": screenplay,
            "input_data":   input_data or {},
            "messages":     [],
            "run_metadata": {
                "run_id":        run_id,
                "project_id":    project_id,
                "started_at":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                "graph_version": "1.0",
            },
        }

        logger.info(
            "WorkflowRunner: starting pipeline",
            extra={
                "run_id":           run_id,
                "project_id":       project_id,
                "screenplay_chars": len(screenplay),
            },
        )

        try:
            graph = self._get_graph()
            final_state: AgentState = await graph.ainvoke(initial_state)
        except Exception as exc:
            logger.error(
                "WorkflowRunner: unhandled graph exception",
                extra={"run_id": run_id, "error": str(exc)},
            )
            raise AgentExecutionError(
                f"Pipeline execution failed for project {project_id}: {exc}"
            ) from exc

        elapsed = round(time.time() - started, 2)
        plan    = final_state.get("production_plan", {})

        logger.info(
            "WorkflowRunner: pipeline complete",
            extra={
                "run_id":       run_id,
                "project_id":   project_id,
                "status":       plan.get("status"),
                "elapsed_secs": elapsed,
            },
        )

        if "run_metadata" in plan:
            plan["run_metadata"]["elapsed_secs"] = elapsed

        return plan


# ---------------------------------------------------------------------------
# Backward-compatible module-level shims
# ``cinepilot_graph`` and ``workflow_runner`` are now lazy proxies.
# Existing code that does:
#   from app.graph.graph import cinepilot_graph, workflow_runner
# continues to work unchanged.
# ---------------------------------------------------------------------------

class _GraphProxy:
    """Proxy that builds the graph on first attribute access."""
    def __getattr__(self, item):
        return getattr(_get_graph(), item)


class _RunnerProxy:
    """Proxy that exposes WorkflowRunner.run() without eagerly building the graph."""
    def __getattr__(self, item):
        global _workflow_runner
        if _workflow_runner is None:
            _workflow_runner = WorkflowRunner()
        return getattr(_workflow_runner, item)

    async def run(self, **kwargs):
        global _workflow_runner
        if _workflow_runner is None:
            _workflow_runner = WorkflowRunner()
        return await _workflow_runner.run(**kwargs)


cinepilot_graph = _GraphProxy()
workflow_runner = _RunnerProxy()
