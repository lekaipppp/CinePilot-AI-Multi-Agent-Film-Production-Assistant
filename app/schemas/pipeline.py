"""
app/schemas/pipeline.py
=======================
Pydantic schemas for the pipeline trigger and result endpoints.

The pipeline endpoint fires the full LangGraph 5-node workflow.
The response wraps the ``production_plan`` dict returned by
``WorkflowRunner.run()`` together with the persisted AgentSession id
so clients can poll for status or retrieve the snapshot later.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Request                                                                       #
# --------------------------------------------------------------------------- #

class PipelineRunRequest(BaseModel):
    """
    Payload for ``POST /pipeline/run``.

    Only ``project_id`` is required — the screenplay is read from
    ``Project.script_draft`` so the client does not have to re-send it.
    ``input_overrides`` allows per-run tuning (e.g. temperature, max_scenes).
    """
    project_id: uuid.UUID = Field(
        ...,
        description="UUID of the project to run the pipeline for.",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    input_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional per-run configuration forwarded to the Director node "
            "(e.g. {\"temperature\": 0.1, \"max_scenes\": 30})."
        ),
    )


# --------------------------------------------------------------------------- #
# Response                                                                      #
# --------------------------------------------------------------------------- #

class RunMetadata(BaseModel):
    """Timing and provenance stamped into every pipeline run."""
    run_id: str
    project_id: str
    started_at: str
    elapsed_secs: Optional[float] = None
    graph_version: str = "1.0"


class PipelineRunResponse(BaseModel):
    """
    Returned immediately after the pipeline finishes.

    ``status`` mirrors ``production_plan["status"]``:
    * ``complete``  — all 5 nodes succeeded.
    * ``partial``   — at least the Director node succeeded; downstream nodes
                      may have partial results.
    * ``failed``    — pipeline could not produce a usable plan.

    ``session_id`` is the persisted ``AgentSession.id`` — clients can use it
    to retrieve the full state snapshot later via ``GET /agents/sessions/{id}``.
    """
    session_id: uuid.UUID = Field(description="ID of the persisted AgentSession row.")
    project_id: uuid.UUID
    status: Literal["complete", "partial", "failed"]
    production_plan: Dict[str, Any] = Field(
        description="Full assembled production plan returned by the output assembler node."
    )
    run_metadata: Optional[RunMetadata] = None
    created_at: datetime


class PipelineStatusResponse(BaseModel):
    """Lightweight poll response for a previously submitted session."""
    session_id: uuid.UUID
    project_id: uuid.UUID
    agent_type: str
    status: str
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
