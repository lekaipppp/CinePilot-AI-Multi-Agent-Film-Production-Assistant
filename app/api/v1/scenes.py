"""
Scenes router – manage scenes within a project.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.scene import SceneCreate, SceneRead, SceneUpdate

router = APIRouter()


@router.get(
    "/{project_id}/scenes",
    response_model=List[SceneRead],
    summary="List scenes for a project",
)
async def list_scenes(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return all scenes belonging to a project. (Service logic to be implemented.)"""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post(
    "/{project_id}/scenes",
    response_model=SceneRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a scene to a project",
)
async def create_scene(
    project_id: uuid.UUID,
    payload: SceneCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new scene for the given project. (Service logic to be implemented.)"""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.patch(
    "/{project_id}/scenes/{scene_id}",
    response_model=SceneRead,
    summary="Update a scene",
)
async def update_scene(
    project_id: uuid.UUID,
    scene_id: uuid.UUID,
    payload: SceneUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partially update a scene. (Service logic to be implemented.)"""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete(
    "/{project_id}/scenes/{scene_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scene",
)
async def delete_scene(
    project_id: uuid.UUID,
    scene_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scene. (Service logic to be implemented.)"""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
