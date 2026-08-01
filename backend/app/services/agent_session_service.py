"""
AgentSessionService – manages CRUD operations for AgentSession records.
Provides a clean interface for the agents layer to read and persist state.
"""

import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_session import AgentSession


class AgentSessionService:
    """Handles persistence of LangGraph agent sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project_id: uuid.UUID, agent_type: str) -> AgentSession:
        session = AgentSession(
            project_id=project_id,
            agent_type=agent_type,
            status="running",
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_or_404(self, session_id: uuid.UUID) -> AgentSession:
        record = await self.db.get(AgentSession, session_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AgentSession {session_id} not found.",
            )
        return record

    async def list_by_project(self, project_id: uuid.UUID) -> List[AgentSession]:
        result = await self.db.execute(
            select(AgentSession)
            .where(AgentSession.project_id == project_id)
            .order_by(AgentSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_state(
        self,
        session_id: uuid.UUID,
        status: str,
        state_snapshot: dict,
        messages: list,
    ) -> AgentSession:
        record = await self.get_or_404(session_id)
        record.status = status
        record.state_snapshot = state_snapshot
        record.messages = messages
        await self.db.flush()
        await self.db.refresh(record)
        return record
