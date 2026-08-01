"""
app/graph/nodes/director_node.py
=================================
Workflow-layer re-export of the Director Agent node.

Why a re-export?
----------------
The canonical node implementation lives in ``app/agents/director/node.py``
where it is co-located with its prompt, schema, parser, and service —
everything the Director Agent needs.

This shim imports it under the name ``director_node`` so
``app/graph/graph.py`` can import all five pipeline nodes from one
consistent package (``app.graph.nodes.*``) without breaking the agent
package's own import surface.

No logic lives here — any change to director behaviour belongs in
``app/agents/director/``.
"""

from __future__ import annotations

from app.agents.director.node import director_node  # noqa: F401 – re-export

__all__ = ["director_node"]
