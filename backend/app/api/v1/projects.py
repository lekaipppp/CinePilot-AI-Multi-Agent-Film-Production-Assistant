"""
Projects router – CRUD endpoints for film production projects.
Business logic is delegated to ProjectService (app/services/project_service.py).
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, status

from app.deps import get_project_service
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailRead,
    ProjectRead,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter()


@router.get(
    "/",
    response_model=List[ProjectRead],
    summary="List all projects",
    description="Return a reverse-chronological paginated list of projects.",
)
async def list_projects(
    limit: int = 20,
    offset: int = 0,
    svc: ProjectService = Depends(get_project_service),
) -> List[ProjectRead]:
    """Return a paginated list of projects ordered by creation date (newest first)."""
    return await svc.list(limit=limit, offset=offset)


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new film production project. Returns the created project.",
)
async def create_project(
    payload: ProjectCreate,
    svc: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Create a new project and return its persisted representation."""
    return await svc.create(payload)


@router.get(
    "/{project_id}",
    response_model=ProjectDetailRead,
    summary="Get full project detail",
    description=(
        "Fetch a single project by UUID with enriched detail: "
        "script availability, scene count, schedule / budget presence, "
        "risk report count, and the latest pipeline session status."
    ),
)
async def get_project(
    project_id: uuid.UUID,
    svc: ProjectService = Depends(get_project_service),
) -> ProjectDetailRead:
    """
    Return a ``ProjectDetailRead`` with derived dashboard fields.

    The ORM relationships are loaded lazily by SQLAlchemy; the service
    assembles the derived boolean/count fields before returning.
    """
    return await svc.get_detail(project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Partially update a project",
    description="Update title, genre, logline, or status. Only provided fields are changed.",
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    svc: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Apply a partial update to the project."""
    return await svc.update(project_id, payload)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description=(
        "Permanently delete a project and all cascaded data "
        "(scenes, locations, schedule, budget, risk reports, agent sessions)."
    ),
)
async def delete_project(
    project_id: uuid.UUID,
    svc: ProjectService = Depends(get_project_service),
) -> None:
    """Delete a project and all its cascaded rows."""
    await svc.delete(project_id)
