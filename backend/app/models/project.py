"""
app/models/project.py
=====================
ORM model for the ``projects`` table — the top-level entity in CinePilot AI.

Schema decisions
----------------
``owner_id``
    Foreign key to ``users.id``.  SET NULL on user delete so projects are
    not destroyed when an account is removed — an admin can reassign them.

``status``
    VARCHAR + CHECK constraint instead of a PostgreSQL ENUM type.  ENUMs
    require ``ALTER TYPE`` to add values; a CHECK constraint is altered with
    a simple ``ALTER TABLE ... DROP CONSTRAINT / ADD CONSTRAINT``.

``script_draft``
    Full text of the AI-generated script stored on the project so it can
    be re-read without re-running the agent.

Indexes
-------
* ``ix_projects_status_created_at`` — list-by-status with time ordering.
* ``ix_projects_owner_id``          — all projects for a given user (FK side).

Relationships (all back-populated)
-----------------------------------
``owner``          → many-to-one  User
``scenes``         → one-to-many  Scene        (cascade delete)
``locations``      → one-to-many  Location     (cascade delete)
``schedule``       → one-to-one   Schedule     (cascade delete, uselist=False)
``budget``         → one-to-one   Budget       (cascade delete, uselist=False)
``risk_reports``   → one-to-many  RiskReport   (cascade delete)
``agent_sessions`` → one-to-many  AgentSession (cascade delete)
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single film production project owned by a User.

    One project owns Scenes, Locations, a Schedule, a Budget,
    RiskReports, and AgentSessions.  All child rows are cascade-deleted
    when the project is removed.
    """

    __tablename__ = "projects"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','in_progress','completed','archived')",
            name="ck_projects_status",
        ),
        Index("ix_projects_status_created_at", "status", "created_at"),
        Index("ix_projects_owner_id", "owner_id"),
    )

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        # SET NULL keeps the project row alive when a user account is deleted
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=False,    # covered by ix_projects_owner_id above
        comment="User who created this project.  NULL if the owner was deleted.",
    )

    # ------------------------------------------------------------------
    # Core columns
    # ------------------------------------------------------------------
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable project title.",
    )
    genre: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Film genre (e.g. 'Thriller', 'Documentary').",
    )
    logline: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="One-sentence story summary.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
        comment="Lifecycle stage: draft | in_progress | completed | archived.",
    )
    script_draft: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full AI-generated script text, stored for re-use without re-running the agent.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    owner: Mapped["User | None"] = relationship(  # noqa: F821
        "User",
        back_populates="projects",
        lazy="select",
        foreign_keys="[Project.owner_id]",
        doc="The user account that owns this project.",
    )
    scenes: Mapped[list["Scene"]] = relationship(  # noqa: F821
        "Scene",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Scene.scene_number",
        doc="Scenes belonging to this project, ordered by scene_number.",
    )
    locations: Mapped[list["Location"]] = relationship(  # noqa: F821
        "Location",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Location.created_at",
        doc="Scouted filming locations for this project.",
    )
    schedule: Mapped["Schedule | None"] = relationship(  # noqa: F821
        "Schedule",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        uselist=False,          # strict one-to-one: a project has at most one schedule
        doc="The shooting schedule generated for this project.",
    )
    budget: Mapped["Budget | None"] = relationship(  # noqa: F821
        "Budget",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        uselist=False,          # one-to-one: a project has at most one budget
        doc="The production budget generated for this project.",
    )
    risk_reports: Mapped[list["RiskReport"]] = relationship(  # noqa: F821
        "RiskReport",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="RiskReport.created_at.desc()",
        doc="Risk analysis reports produced for this project.",
    )
    agent_sessions: Mapped[list["AgentSession"]] = relationship(  # noqa: F821
        "AgentSession",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="AgentSession.created_at.desc()",
        doc="LangGraph agent execution sessions for this project.",
    )
