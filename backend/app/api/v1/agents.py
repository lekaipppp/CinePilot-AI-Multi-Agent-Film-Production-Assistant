"""
Agents router – trigger and inspect multi-agent LangGraph workflows.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.agent_session import AgentRunRequest, AgentSessionRead

router = APIRouter()


@router.post(
    "/run",
    response_model=AgentSessionRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an agent workflow",
)
async def run_agent(
    payload: AgentRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Dispatch a LangGraph agent workflow asynchronously.
    Returns the newly created AgentSession record.
    (Graph wiring to be implemented in app/graph/.)
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get(
    "/sessions/{session_id}",
    response_model=AgentSessionRead,
    summary="Get agent session status",
)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch the current state and messages of an agent session."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get(
    "/sessions",
    response_model=list[AgentSessionRead],
    summary="List agent sessions for a project",
)
async def list_sessions(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return all agent sessions scoped to the given project."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
