"""
app/graph/edges.py
==================
Conditional edge routing for the CinePilot LangGraph pipeline.

LangGraph supports two kinds of edges:

    add_edge(from, to)
        Unconditional — always transitions from → to.

    add_conditional_edges(from, routing_fn, {return_value: next_node})
        Conditional — ``routing_fn(state)`` returns a string key;
        the graph looks up the next node in the provided mapping.

This module owns all routing functions so ``graph.py`` stays free of
branching logic.

Current routing strategy
------------------------
Every node in this pipeline uses the same strategy:

    if state has a non-empty "error" key → route to "error_handler"
    else                                  → route to the nominated next node

This lets the graph gracefully degrade on partial failures: a node
sets ``state["error"]`` and returns; all subsequent nodes skip their
work and pass state through unchanged; the output assembler records
the error in the production plan.

Adding more sophisticated routing (parallel branches, retries, human-in-
the-loop checkpoints) requires only adding new routing functions here
and updating ``graph.py`` — no other file needs to change.
"""

from __future__ import annotations

from typing import Literal

from app.graph.state import AgentState

# ---------------------------------------------------------------------------
# Sentinel values returned by routing functions
# These strings are used as keys in add_conditional_edges() maps.
# ---------------------------------------------------------------------------
CONTINUE      = "continue"
ERROR_HANDLER = "error_handler"


# ---------------------------------------------------------------------------
# Generic error-aware router factory
# ---------------------------------------------------------------------------

def make_error_router(
    next_node: str,
) -> "RoutingFn":
    """
    Return a routing function that sends state to ``next_node`` on
    success or to ``"error_handler"`` if ``state["error"]`` is set.

    Parameters
    ----------
    next_node:
        The node name to route to on the happy path.

    Returns
    -------
    RoutingFn
        A zero-argument-capture closure suitable for
        ``graph.add_conditional_edges(..., routing_fn, ...)``.
    """

    def _router(state: AgentState) -> str:
        if state.get("error"):
            return ERROR_HANDLER
        return next_node

    _router.__name__ = f"route_to_{next_node}"
    return _router


# ---------------------------------------------------------------------------
# Per-transition routing functions
# ---------------------------------------------------------------------------
# Defined explicitly (rather than always using make_error_router) so they
# have stable, readable names in LangGraph's compiled graph visualization.

def route_after_director(state: AgentState) -> str:
    """Route from ``director`` → ``location`` or ``error_handler``."""
    return ERROR_HANDLER if state.get("error") else "location"


def route_after_location(state: AgentState) -> str:
    """Route from ``location`` → ``scheduler`` or ``error_handler``."""
    return ERROR_HANDLER if state.get("error") else "scheduler"


def route_after_scheduler(state: AgentState) -> str:
    """Route from ``scheduler`` → ``budget`` or ``error_handler``."""
    return ERROR_HANDLER if state.get("error") else "budget"


def route_after_budget(state: AgentState) -> str:
    """Route from ``budget`` → ``risk`` or ``error_handler``."""
    return ERROR_HANDLER if state.get("error") else "risk"


def route_after_risk(state: AgentState) -> str:
    """Route from ``risk`` → ``assemble_output`` or ``error_handler``."""
    return ERROR_HANDLER if state.get("error") else "assemble_output"


# ---------------------------------------------------------------------------
# Type alias (for documentation purposes)
# ---------------------------------------------------------------------------
from typing import Callable
RoutingFn = Callable[[AgentState], str]
