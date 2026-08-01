"""
app/schemas/script.py
=====================
Pydantic schemas for script upload and retrieval endpoints.

The screenplay text lives on the ``Project.script_draft`` column,
so these schemas are deliberately thin wrappers — no dedicated
``scripts`` table exists.
"""

from typing import Optional
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Request                                                                       #
# --------------------------------------------------------------------------- #

class ScriptUploadRequest(BaseModel):
    """
    Payload for ``POST /script/upload-script``.

    ``screenplay`` is the full plain-text or Fountain-formatted script.
    It is stored verbatim on ``Project.script_draft`` so the pipeline
    can re-read it without re-running the agent.
    """
    project_id: str = Field(
        ...,
        description="UUID of the project this script belongs to.",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    screenplay: str = Field(
        ...,
        min_length=50,
        description="Full screenplay text (plain text or Fountain format). Minimum 50 characters.",
    )


# --------------------------------------------------------------------------- #
# Response                                                                      #
# --------------------------------------------------------------------------- #

class ScriptUploadResponse(BaseModel):
    """
    Returned after a successful script upload.
    Confirms the project ID and the stored character count.
    """
    project_id: str
    message: str
    character_count: int
    screenplay_preview: Optional[str] = Field(
        default=None,
        description="First 200 characters of the stored screenplay for quick confirmation.",
    )
