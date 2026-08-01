"""
app/models/agent_session.py
===========================
ORM model for the ``agent_sessions`` table.

An AgentSession persists the full LangGraph state for one execution of
the multi-agent pipeline.  It is the source of truth for:
* Which agent type was run and its current lifecycle status.
* The ``state_snapshot`` (the entire ``AgentState`` dict at the last checkpoint).
* The ``messages`` list (ordered conversation / tool-call history).
* Timing information for performance analysis.

Schema decisions
----------------
* ``status`` has a CHECK constraint and an index because polling queries
  like "find all running sessions" are expected to be common.
* ``state_snapshot`` and ``messages`` are JSONB — Postgres can index and
  query inside them if needed (e.g. ``state_snapshot->'scenes' IS NOT NULL``).
* ``error_message`` is a dedicated nullable text column rather than burying
  errors inside JSONB — makes failure queries and alerting simpler.
* ``completed_at`` is nullable — set only when status becomes terminal.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Persists the state of a single multi-agent LangGraph execution.

    Lifecycle: pending → running → completed | failed
    """

    __tablename__ = "agent_sessions"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','running','completed','failed')",
            name="ck_agent_sessions_status",
        ),
        # Most frequent query: "all sessions for project X that are running"
        Index("ix_agent_sessions_project_id_status", "project_id", "status"),
        # Reverse-chronological listing by project
        Index("ix_agent_sessions_project_id_created_at", "project_id", "created_at"),
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
    # Session metadata
    # ------------------------------------------------------------------
    agent_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "Identifier for the agent pipeline that was run, e.g. "
            "'full_pipeline', 'location_scout', 'script_writer'."
        ),
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Lifecycle stage: pending | running | completed | failed.",
    )

    # ------------------------------------------------------------------
    # LangGraph state persistence
    # ------------------------------------------------------------------
    state_snapshot: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Full AgentState dict captured at the last graph checkpoint.",
    )
    messages: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Ordered list of LangChain BaseMessage dicts.",
    )

    # ------------------------------------------------------------------
    # Outcome tracking
    # ------------------------------------------------------------------
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable error if status='failed'.",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the session reached a terminal state.",
    )

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="agent_sessions",
        lazy="select",
    )
