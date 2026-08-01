"""
app/schemas/schedule.py
=======================
Pydantic schemas for Schedule and ScheduleDay endpoints.

Mirrors app/models/schedule.py.  ``scene_ids`` is represented as a plain
``List[str]`` in the schema (UUIDs serialised to strings) matching the JSONB
array stored in the ORM model.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ScheduleStatus = Literal["draft", "approved", "in_progress", "completed"]


# --------------------------------------------------------------------------- #
# ScheduleDay schemas                                                           #
# --------------------------------------------------------------------------- #

class ScheduleDayBase(BaseModel):
    shoot_date: date
    day_number: int = Field(..., ge=1)
    scene_ids: Optional[List[str]] = Field(
        default=None,
        description="Ordered list of Scene UUID strings to film on this day.",
    )
    notes: Optional[str] = None
    call_time: Optional[str] = Field(
        default=None,
        pattern=r"^\d{2}:\d{2}$",
        description="Crew call time in HH:MM (24-hour) format.",
    )
    estimated_wrap_time: Optional[str] = Field(
        default=None,
        pattern=r"^\d{2}:\d{2}$",
        description="Estimated wrap time in HH:MM (24-hour) format.",
    )


class ScheduleDayRead(ScheduleDayBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    schedule_id: uuid.UUID
    location_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Schedule schemas                                                              #
# --------------------------------------------------------------------------- #

class ScheduleRead(BaseModel):
    """
    Full schedule representation, including all shoot days.
    Returned by ``GET /schedule/{project_id}``.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    total_shoot_days: Optional[int] = None
    status: str
    notes: Optional[str] = None
    days: List[ScheduleDayRead] = []
    created_at: datetime
    updated_at: datetime
