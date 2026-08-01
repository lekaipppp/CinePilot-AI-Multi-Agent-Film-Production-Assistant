"""
app/api/v1/schedule.py
=======================
Schedule router – retrieve the AI-generated shooting schedule for a project.

Routes
------
GET /schedule/{project_id}   Retrieve the full schedule with all shoot days.

Schedules are created exclusively by the LangGraph scheduler_node; this
router is read-only.  All business logic is in ScheduleService.
"""

import uuid

from fastapi import APIRouter, Depends

from app.deps import get_schedule_service
from app.schemas.schedule import ScheduleRead
from app.services.schedule_service import ScheduleService

router = APIRouter()


@router.get(
    "/{project_id}",
    response_model=ScheduleRead,
    summary="Get shooting schedule for a project",
    description=(
        "Returns the full shooting schedule — including all shoot days with "
        "dates, scene assignments, and call times — for the given project. "
        "Returns 404 if no schedule has been generated yet (run the pipeline first)."
    ),
)
async def get_schedule(
    project_id: uuid.UUID,
    svc: ScheduleService = Depends(get_schedule_service),
) -> ScheduleRead:
    """Fetch the Schedule and its ScheduleDay rows for the given project."""
    return await svc.get_by_project(project_id)
