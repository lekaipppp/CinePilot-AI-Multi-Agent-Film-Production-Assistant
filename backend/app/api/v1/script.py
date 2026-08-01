"""
app/api/v1/script.py
====================
Script router – upload and retrieve a project's screenplay.

Routes
------
POST /script/upload-script   Upload (or overwrite) a project's screenplay.
GET  /script/{project_id}    Retrieve the stored screenplay for a project.

All business logic is delegated to ScriptService via the deps.py dependency.
Routers are kept thin: validate input → call service → return response.
"""

import uuid

from fastapi import APIRouter, Depends, status

from app.deps import get_script_service
from app.schemas.script import ScriptUploadRequest, ScriptUploadResponse
from app.services.script_service import ScriptService

router = APIRouter()

_PREVIEW_LENGTH = 200   # characters shown in the upload confirmation


@router.post(
    "/upload-script",
    response_model=ScriptUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload or overwrite a project's screenplay",
    description=(
        "Stores the provided screenplay text on the Project row. "
        "Calling this endpoint again overwrites the previous draft. "
        "The screenplay must be uploaded before the pipeline can be triggered."
    ),
)
async def upload_script(
    payload: ScriptUploadRequest,
    svc: ScriptService = Depends(get_script_service),
) -> ScriptUploadResponse:
    """
    Persist ``payload.screenplay`` on ``Project.script_draft``.

    Returns a lightweight confirmation with a preview of the stored text.
    """
    project = await svc.upload(
        project_id=uuid.UUID(payload.project_id),
        screenplay=payload.screenplay,
    )
    return ScriptUploadResponse(
        project_id=str(project.id),
        message="Screenplay uploaded successfully.",
        character_count=len(project.script_draft),
        screenplay_preview=project.script_draft[:_PREVIEW_LENGTH],
    )


@router.get(
    "/{project_id}",
    summary="Retrieve stored screenplay for a project",
    description=(
        "Returns the raw screenplay text stored on the project. "
        "Returns 404 if no script has been uploaded yet."
    ),
    response_model=ScriptUploadResponse,
)
async def get_script(
    project_id: uuid.UUID,
    svc: ScriptService = Depends(get_script_service),
) -> ScriptUploadResponse:
    """Fetch the screenplay text for the given project."""
    from fastapi import HTTPException

    script = await svc.get_script(project_id=project_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No screenplay found for project {project_id}.",
        )
    return ScriptUploadResponse(
        project_id=str(project_id),
        message="Screenplay retrieved successfully.",
        character_count=len(script),
        screenplay_preview=script[:_PREVIEW_LENGTH],
    )
