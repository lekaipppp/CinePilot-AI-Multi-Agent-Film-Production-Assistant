"""
app/services/schedule_service.py
=================================
ScheduleService – fetches the shooting schedule for a project.

Responsibility
--------------
Schedules are created exclusively by the ``scheduler_node`` inside the
LangGraph pipeline.  This service is read-only from the API perspective —
its single public method retrieves the Schedule with its days eagerly loaded
so the router can serialise the full response in one query.

All reads are SELECT-only; no flush / commit is required.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.schedule import Schedule
from app.services.project_service import ProjectService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ScheduleService:
    """Handles retrieval of Schedule entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._project_svc = ProjectService(db)

    async def get_by_project(self, project_id: uuid.UUID) -> Schedule:
        """
        Return the Schedule row (with all days) for the given project.

        Parameters
        ----------
        project_id:
            UUID of the project whose schedule to retrieve.

        Returns
        -------
        Schedule
            The Schedule ORM instance with ``days`` eagerly loaded and ordered
            by ``shoot_date`` (enforced by the ORM relationship definition).

        Raises
        ------
        HTTPException 404
            When the project does not exist, or when no schedule has been
            generated yet (run the pipeline first).
        """
        # Confirm the project exists first (raises 404 if not)
        await self._project_svc.get_or_404(project_id)

        result = await self.db.execute(
            select(Schedule)
            .where(Schedule.project_id == project_id)
            .options(selectinload(Schedule.days))
        )
        schedule = result.scalar_one_or_none()
        if schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No schedule found for project {project_id}. "
                    "Run the pipeline first."
                ),
            )

        logger.debug(
            "ScheduleService: retrieved schedule",
            extra={
                "project_id": str(project_id),
                "schedule_id": str(schedule.id),
                "days": len(schedule.days),
            },
        )
        return schedule
