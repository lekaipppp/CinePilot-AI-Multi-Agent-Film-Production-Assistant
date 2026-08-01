"""
app/graph/__init__.py
=====================
Public surface of the graph package.

All exports are lazy — importing this module never triggers LangGraph,
Gemini SDK, or database initialisation.
"""

from app.graph.state import AgentState
from app.graph.graph import (
    cinepilot_graph,
    workflow_runner,
    WorkflowRunner,
    build_graph,
)

__all__ = [
    "AgentState",
    "cinepilot_graph",
    "workflow_runner",
    "WorkflowRunner",
    "build_graph",
]
