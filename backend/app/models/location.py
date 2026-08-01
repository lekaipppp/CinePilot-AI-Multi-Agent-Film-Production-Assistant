"""
app/models/location.py
======================
ORM model for the ``locations`` table.

A Location is a real-world filming candidate discovered and scored by the
LocationScoutAgent.  It belongs to a Project and can be referenced by one
or many Scenes.

Design decisions
----------------
``coordinates``
    PostgreSQL stores lat/lng as two separate FLOAT columns rather than a
    PostGIS POINT so the project has no PostGIS dependency.  Rename to a
    geography column in a migration if spatial queries are needed later.

``place_id``
    Google Places stable identifier.  Unique *per project* — the same
    physical location can appear in multiple projects (different rows).
    A global unique constraint would prevent that, so we scope it.

``weather_data``
    Full OpenWeather JSON cached here so agents don't re-fetch.

``ai_suitability_score``
    0–10 float assigned by Gemini representing how well this location fits
    the project's visual requirements.

``status``
    draft  → under consideration
    scouted → visited/confirmed by production team
    approved → selected for filming
    rejected → ruled out

Indexes
-------
* ``ix_locations_project_id`` — fetch all locations for a project.
* ``ix_locations_status``     — filter by approval stage.
* ``uq_locations_project_place`` — one row per Google Place per project.

Relationships
-------------
``project``  → many-to-one  Project
``scenes``   → one-to-many  Scene  (a location can serve multiple scenes)
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Location(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A real-world filming location candidate scouted for a project.

    Lifecycle: draft → scouted → approved | rejected
    """

    __tablename__ = "locations"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','scouted','approved','rejected')",
            name="ck_locations_status",
        ),
        CheckConstraint(
            "ai_suitability_score IS NULL OR "
            "(ai_suitability_score >= 0 AND ai_suitability_score <= 10)",
            name="ck_locations_suitability_score_range",
        ),
        # Prevent duplicate Google Place entries within the same project
        UniqueConstraint(
            "project_id", "place_id",
            name="uq_locations_project_place",
        ),
        Index("ix_locations_project_id", "project_id"),
        Index("ix_locations_status",     "status"),
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owning project.",
    )

    # ------------------------------------------------------------------
    # Identity / origin
    # ------------------------------------------------------------------
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable location name (e.g. 'Griffith Observatory').",
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full formatted address string from Google Places.",
    )
    place_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Google Places stable place identifier.",
    )

    # ------------------------------------------------------------------
    # Coordinates
    # ------------------------------------------------------------------
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="WGS-84 latitude  (-90 to +90).",
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="WGS-84 longitude (-180 to +180).",
    )

    # ------------------------------------------------------------------
    # Descriptive metadata
    # ------------------------------------------------------------------
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Freeform notes about the location (access, permits, etc.).",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
        comment="Approval stage: draft | scouted | approved | rejected.",
    )

    # ------------------------------------------------------------------
    # AI / external API data
    # ------------------------------------------------------------------
    ai_suitability_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Gemini-assigned suitability score (0–10).",
    )
    ai_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Gemini-generated narrative about why this location fits the project.",
    )
    weather_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Cached OpenWeather forecast JSON for this coordinate.",
    )
    places_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Raw Google Places API result object for this location.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="locations",
        lazy="select",
    )
    scenes: Mapped[list["Scene"]] = relationship(  # noqa: F821
        "Scene",
        back_populates="location",
        lazy="select",
        doc="Scenes assigned to this filming location.",
    )
