"""
app/api/v1/pipeline.py
=======================
Pipeline router – trigger and poll the multi-agent production planning graph.

Routes
------
POST /pipeline/run          Trigger a full pipeline run for a project.
GET  /pipeline/status/{id}  Poll the status of a previously submitted session.

The heavy work (LangGraph execution) happens inside ``PipelineService.run()``.
This router is responsible only for request validation and response shaping.
"""

from __future__ import annotations

import uuid
from datetime import timezone

from fastapi import APIRouter, Depends, status

from app.deps import get_agent_session_service, get_pipeline_service
from app.schemas.pipeline import (
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineStatusResponse,
    RunMetadata,
)
from app.services.agent_session_service import AgentSessionService
from app.services.pipeline_service import PipelineService

router = APIRouter()


@router.post(
    "/run",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the full multi-agent production planning pipeline",
    description=(
        "Executes the 5-node LangGraph pipeline (Director → Location Scout → "
        "Scheduler → Budget → Risk Analyst) for the specified project. "
        "The project must have a screenplay uploaded before calling this endpoint. "
        "This is a synchronous call — the response is returned once the graph finishes "
        "(typically 20–60 seconds). "
        "The ``session_id`` in the response can be used to retrieve the full "
        "state snapshot later via GET /pipeline/status/{session_id}."
    ),
)
async def run_pipeline(
    payload: PipelineRunRequest,
    svc: PipelineService = Depends(get_pipeline_service),
) -> PipelineRunResponse:
    """
    Trigger a full pipeline run and wait for the result.

    Returns the assembled ``production_plan`` and the persisted session ID.
    """
    agent_session = await svc.run(
        project_id=payload.project_id,
        input_overrides=payload.input_overrides,
    )

    plan = agent_session.state_snapshot or {}
    plan_status = plan.get("status", "failed")

    # Extract run_metadata from the plan if the graph wrote it
    raw_meta = plan.get("run_metadata")
    run_meta = RunMetadata(**raw_meta) if raw_meta else None

    return PipelineRunResponse(
        session_id=agent_session.id,
        project_id=payload.project_id,
        status=plan_status,
        production_plan=plan,
        run_metadata=run_meta,
        created_at=agent_session.created_at,
    )


@router.get(
    "/status/{session_id}",
    response_model=PipelineStatusResponse,
    summary="Poll the status of a pipeline session",
    description=(
        "Returns the current lifecycle status of a previously submitted "
        "pipeline session (pending → running → completed | failed). "
        "Use this endpoint to implement polling while a long-running pipeline "
        "is executing."
    ),
)
async def get_pipeline_status(
    session_id: uuid.UUID,
    svc: AgentSessionService = Depends(get_agent_session_service),
) -> PipelineStatusResponse:
    """Fetch the current status of an AgentSession by its ID."""
    session = await svc.get_or_404(session_id)
    return PipelineStatusResponse(
        session_id=session.id,
        project_id=session.project_id,
        agent_type=session.agent_type,
        status=session.status,
        error_message=session.error_message,
        completed_at=session.completed_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
