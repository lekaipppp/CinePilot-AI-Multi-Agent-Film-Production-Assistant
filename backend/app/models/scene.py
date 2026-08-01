"""
app/models/scene.py
===================
ORM model for the ``scenes`` table.

A Scene is a discrete unit of a film script that belongs to one Project.

Changes from the previous version
----------------------------------
* ``location_id`` FK added — optionally points at the approved Location
  chosen for this scene.  The FK is nullable so scenes can exist before
  location scouting is complete.  ``SET NULL`` on location delete preserves
  the scene row.
* JSONB agent-data columns retained for backward compatibility while the
  agent populates them; the canonical location record is the Location row.
* ``int_ext`` and ``time_of_day`` remain as validated VARCHAR columns with
  CHECK constraints for fast server-side filtering.

Indexes
-------
* ``uq_scenes_project_scene_number`` — no duplicate scene numbers per project.
* ``ix_scenes_project_id``           — list scenes for a project.
* ``ix_scenes_location_id``          — list scenes at a given location.

Relationships
-------------
``project``  → many-to-one  Project
``location`` → many-to-one  Location (nullable)
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
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


class Scene(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A discrete scene within a film production project.

    Populated in two phases:
    1. User-provided: ``scene_number``, ``title``, ``description``,
       ``location_query``, ``int_ext``, ``time_of_day``.
    2. Agent-populated / linked: ``location_id``, ``location_data``,
       ``weather_data``, ``ai_suggestions``.
    """

    __tablename__ = "scenes"

    __table_args__ = (
        UniqueConstraint(
            "project_id", "scene_number",
            name="uq_scenes_project_scene_number",
        ),
        CheckConstraint(
            "int_ext IN ('INT', 'EXT', 'INT/EXT') OR int_ext IS NULL",
            name="ck_scenes_int_ext",
        ),
        CheckConstraint(
            "time_of_day IN ('DAY', 'NIGHT', 'DUSK', 'DAWN') OR time_of_day IS NULL",
            name="ck_scenes_time_of_day",
        ),
        Index("ix_scenes_project_id",  "project_id"),
        Index("ix_scenes_location_id", "location_id"),
    )

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owning project.",
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        # SET NULL preserves the scene if the location record is deleted
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=False,    # covered by ix_scenes_location_id above
        comment="The approved filming location chosen for this scene (nullable).",
    )

    # ------------------------------------------------------------------
    # User-supplied columns
    # ------------------------------------------------------------------
    scene_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="1-based sequential scene number within the project.",
    )
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Short scene heading (e.g. 'INT. DETECTIVE OFFICE – DAY').",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Scene action lines / brief.",
    )
    location_query: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Search string sent to Google Maps / Places.",
    )
    int_ext: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Interior/exterior flag: INT | EXT | INT/EXT.",
    )
    time_of_day: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Lighting condition: DAY | NIGHT | DUSK | DAWN.",
    )

    # ------------------------------------------------------------------
    # Agent-populated JSONB columns
    # ------------------------------------------------------------------
    location_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Google Places API response for the scouted location.",
    )
    weather_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="OpenWeather current + forecast data for the location.",
    )
    ai_suggestions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Gemini-generated shooting suggestions for this scene.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="scenes",
        lazy="select",
    )
    location: Mapped["Location | None"] = relationship(  # noqa: F821
        "Location",
        back_populates="scenes",
        lazy="select",
        foreign_keys=[location_id],
        doc="The Location row chosen for this scene.",
    )
