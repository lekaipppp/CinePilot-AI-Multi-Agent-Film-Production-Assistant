"""
ProjectService – orchestrates all business logic for Project entities.
Sits between the router layer and the repository / database layer.
"""

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectDetailRead, ProjectUpdate


class ProjectService:
    """Encapsulates Project CRUD and domain rules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, limit: int = 20, offset: int = 0) -> List[Project]:
        result = await self.db.execute(
            select(Project).offset(offset).limit(limit).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_or_404(self, project_id: uuid.UUID) -> Project:
        project = await self.db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found.",
            )
        return project

    async def get_detail(self, project_id: uuid.UUID) -> ProjectDetailRead:
        """
        Return a ``ProjectDetailRead`` with all dashboard-level derived fields.

        Eagerly loads scenes, schedule, budget, risk_reports, and agent_sessions
        in a single query using ``selectinload`` to avoid N+1 issues.
        """
        result = await self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.scenes),
                selectinload(Project.schedule),
                selectinload(Project.budget),
                selectinload(Project.risk_reports),
                selectinload(Project.agent_sessions),
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found.",
            )

        # Derive the latest session status (sessions ordered desc by created_at)
        latest_status: Optional[str] = None
        if project.agent_sessions:
            latest_status = project.agent_sessions[0].status

        return ProjectDetailRead(
            id=project.id,
            title=project.title,
            genre=project.genre,
            logline=project.logline,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            has_script=bool(project.script_draft),
            script_preview=project.script_draft[:300] if project.script_draft else None,
            scene_count=len(project.scenes),
            has_schedule=project.schedule is not None,
            has_budget=project.budget is not None,
            risk_report_count=len(project.risk_reports),
            latest_session_status=latest_status,
        )

    async def create(self, payload: ProjectCreate) -> Project:
        project = Project(**payload.model_dump())
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project_id: uuid.UUID, payload: ProjectUpdate) -> Project:
        project = await self.get_or_404(project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: uuid.UUID) -> None:
        project = await self.get_or_404(project_id)
        await self.db.delete(project)
        await self.db.flush()
