"""
app/models/schedule.py
======================
ORM models for the ``schedules`` and ``schedule_days`` tables.

A Schedule is the AI-generated shooting schedule for a Project.
It contains an ordered list of ScheduleDay rows, each describing what
scenes will be filmed on a given date and at which location.

Design decisions
----------------
``Schedule`` (one-to-one with Project)
    Stores high-level metadata: total shoot days, currency for per-diem
    estimates, and a free-text ``notes`` field for production insights.
    ``status`` mirrors the project lifecycle so the UI can show schedule
    health at a glance.

``ScheduleDay`` (one-to-many with Schedule)
    One row per calendar day of the shoot.
    ``scene_ids`` is a JSONB array of Scene UUIDs (as strings) rather than
    a join table because:
    * The order of scenes within a day matters and is captured naturally
      in the array.
    * Scene assignments change frequently during pre-production; a JSONB
      column is trivially updated with a single write.
    * Full relational join-table normalisation would add 2 extra tables
      and JOIN complexity with no query benefit at this scale.
    ``location_id`` is a nullable FK — a day may involve travel between
    locations, in which case the agent leaves it NULL and describes it in
    ``notes``.

Indexes
-------
* ``ix_schedules_project_id``          — look up a project's schedule.
* ``ix_schedule_days_schedule_id``      — all days for a schedule.
* ``ix_schedule_days_shoot_date``       — calendar view filtering.
* ``uq_schedule_days_schedule_date``    — no duplicate dates in one schedule.

Relationships
-------------
``Schedule.project``       → one-to-one   Project (back)
``Schedule.days``          → one-to-many  ScheduleDay (cascade delete)
``ScheduleDay.schedule``   → many-to-one  Schedule
``ScheduleDay.location``   → many-to-one  Location (nullable)
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

class Schedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    The AI-generated shooting schedule for a project.

    One schedule per project (one-to-one enforced at the application layer
    via ``uselist=False`` on the Project side).
    """

    __tablename__ = "schedules"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','approved','in_progress','completed')",
            name="ck_schedules_status",
        ),
        Index("ix_schedules_project_id", "project_id"),
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,        # enforces the one-to-one at the DB level
        comment="Owning project (unique — one schedule per project).",
    )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    total_shoot_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total number of scheduled filming days.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
        comment="Schedule stage: draft | approved | in_progress | completed.",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="General production insights and scheduling rationale from the agent.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="schedule",
        lazy="select",
    )
    days: Mapped[list["ScheduleDay"]] = relationship(
        "ScheduleDay",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ScheduleDay.shoot_date",
        doc="Ordered list of individual shooting days.",
    )


# ---------------------------------------------------------------------------
# ScheduleDay
# ---------------------------------------------------------------------------

class ScheduleDay(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    One calendar day in a shooting schedule.

    ``scene_ids``   — ordered JSONB array of Scene UUID strings to film that day.
    ``location_id`` — primary location for the day (NULL if multi-location).
    """

    __tablename__ = "schedule_days"

    __table_args__ = (
        # No two days with the same date within the same schedule
        UniqueConstraint(
            "schedule_id", "shoot_date",
            name="uq_schedule_days_schedule_date",
        ),
        Index("ix_schedule_days_schedule_id", "schedule_id"),
        Index("ix_schedule_days_shoot_date",  "shoot_date"),
    )

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent schedule.",
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Primary filming location for the day (NULL if multi-location).",
    )

    # ------------------------------------------------------------------
    # Day details
    # ------------------------------------------------------------------
    shoot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Calendar date for this shoot day (YYYY-MM-DD).",
    )
    day_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential day number within the schedule (1-based).",
    )
    scene_ids: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment=(
            "Ordered JSONB array of Scene UUID strings to be filmed on this day.  "
            "Order within the array is the planned shooting order."
        ),
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Day-specific production notes (crew call time, weather contingency, etc.).",
    )
    call_time: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Crew call time in HH:MM (24-hour) format.",
    )
    estimated_wrap_time: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Estimated wrap time in HH:MM (24-hour) format.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    schedule: Mapped["Schedule"] = relationship(
        "Schedule",
        back_populates="days",
        lazy="select",
    )
    location: Mapped["Location | None"] = relationship(  # noqa: F821
        "Location",
        lazy="select",
        foreign_keys=[location_id],
        doc="Primary location for this shoot day.",
    )
