"""
Pydantic schemas for Project.
Separates API contract (schemas) from DB contract (models).
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# --------------------------------------------------------------------------- #
# Base                                                                         #
# --------------------------------------------------------------------------- #
class ProjectBase(BaseModel):
    title: str
    genre: Optional[str] = None
    logline: Optional[str] = None


# --------------------------------------------------------------------------- #
# Request bodies                                                                #
# --------------------------------------------------------------------------- #
class ProjectCreate(ProjectBase):
    """Payload accepted when creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """All fields optional for partial updates (PATCH semantics)."""
    title: Optional[str] = None
    genre: Optional[str] = None
    logline: Optional[str] = None
    status: Optional[str] = None


# --------------------------------------------------------------------------- #
# Response bodies                                                               #
# --------------------------------------------------------------------------- #
class ProjectRead(ProjectBase):
    """Lean project representation returned in list responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectDetailRead(ProjectRead):
    """
    Full project detail including the stored screenplay and nested child counts.

    Returned by ``GET /projects/{project_id}`` so the client has everything
    it needs to render the project dashboard without extra round-trips.

    ``has_script``            — True when ``script_draft`` is populated.
    ``script_preview``        — First 300 characters of the script for quick
                                confirmation; the full text is not included to
                                keep the response lean.
    ``scene_count``           — How many scenes have been extracted.
    ``has_schedule``          — Whether a Schedule row exists for this project.
    ``has_budget``            — Whether a Budget row exists for this project.
    ``risk_report_count``     — Total number of risk analysis runs.
    ``latest_session_status`` — Status of the most recent AgentSession, or
                                None if no pipeline has been run yet.
    """
    model_config = ConfigDict(from_attributes=True)

    has_script: bool = False
    script_preview: Optional[str] = None
    scene_count: int = 0
    has_schedule: bool = False
    has_budget: bool = False
    risk_report_count: int = 0
    latest_session_status: Optional[str] = None
