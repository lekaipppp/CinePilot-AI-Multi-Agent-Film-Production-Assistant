"""
app/models/risk_report.py
=========================
ORM models for the ``risk_reports`` and ``risk_items`` tables.

A RiskReport is an AI-generated analysis of production risks for a Project.
A project can have multiple RiskReports (one per agent run), so their history
is preserved and the latest report can always be identified by ``created_at``.
Each report contains a list of RiskItem rows describing individual risks.

Design decisions
----------------
``RiskReport`` (one-to-many with Project)
    Intentionally *not* one-to-one — the risk agent may be re-run as the
    project evolves (new locations added, schedule changes, etc.) and keeping
    older snapshots provides an audit trail.
    ``overall_risk_level`` is a high-level summary: low / medium / high /
    critical — useful for dashboard colouring without reading all items.

``RiskItem`` (one-to-many with RiskReport)
    One row per identified risk.
    ``category``  — the area of production affected (weather, budget, legal…).
    ``probability`` / ``impact`` — 1–5 integer scales so the application can
    compute a numeric risk score (probability × impact) for sorting.
    ``mitigation`` — actionable recommendation from the agent.
    ``status``    — tracks whether the team has acknowledged / resolved the risk.

Risk score formula (computed in application layer, not stored):
    risk_score = probability × impact   (range 1–25)
    1–4  → low      5–9  → medium
    10–16 → high    17–25 → critical

Indexes
-------
* ``ix_risk_reports_project_id``           — all reports for a project.
* ``ix_risk_reports_overall_risk_level``   — filter by severity.
* ``ix_risk_items_report_id``              — all items for a report.
* ``ix_risk_items_category``               — filter/group by category.
* ``ix_risk_items_status``                 — filter unresolved risks.

Relationships
-------------
``RiskReport.project``    → many-to-one  Project (back)
``RiskReport.items``      → one-to-many  RiskItem (cascade delete)
``RiskItem.report``       → many-to-one  RiskReport
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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# RiskReport
# ---------------------------------------------------------------------------

class RiskReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A snapshot of identified production risks at a point in time.

    Multiple reports per project are allowed so risk evolution can be tracked
    as the project progresses through pre-production.
    """

    __tablename__ = "risk_reports"

    __table_args__ = (
        CheckConstraint(
            "overall_risk_level IN ('low','medium','high','critical')",
            name="ck_risk_reports_overall_risk_level",
        ),
        Index("ix_risk_reports_project_id",         "project_id"),
        Index("ix_risk_reports_overall_risk_level",  "overall_risk_level"),
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
    # Report-level summary
    # ------------------------------------------------------------------
    overall_risk_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Aggregate risk rating: low | medium | high | critical.",
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Agent-generated executive summary of all identified risks.",
    )
    recommendations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Top-level mitigation recommendations from the agent.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="risk_reports",
        lazy="select",
    )
    items: Mapped[list["RiskItem"]] = relationship(
        "RiskItem",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Individual risk items ordered by severity (probability × impact).",
    )


# ---------------------------------------------------------------------------
# RiskItem
# ---------------------------------------------------------------------------

class RiskItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single identified production risk within a RiskReport.

    Risk score = probability × impact   (1–25 scale).
    """

    __tablename__ = "risk_items"

    __table_args__ = (
        CheckConstraint(
            "category IN ("
            "'weather','budget','schedule','legal_permits',"
            "'cast_crew','equipment','location','health_safety','other'"
            ")",
            name="ck_risk_items_category",
        ),
        CheckConstraint(
            "probability BETWEEN 1 AND 5",
            name="ck_risk_items_probability_range",
        ),
        CheckConstraint(
            "impact BETWEEN 1 AND 5",
            name="ck_risk_items_impact_range",
        ),
        CheckConstraint(
            "status IN ('open','acknowledged','mitigated','closed')",
            name="ck_risk_items_status",
        ),
        Index("ix_risk_items_report_id", "report_id"),
        Index("ix_risk_items_category",  "category"),
        Index("ix_risk_items_status",    "status"),
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("risk_reports.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent risk report.",
    )

    # ------------------------------------------------------------------
    # Risk identification
    # ------------------------------------------------------------------
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Short, descriptive risk title (e.g. 'Rain forecast on exterior shoot day').",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment=(
            "Production area affected: weather | budget | schedule | "
            "legal_permits | cast_crew | equipment | location | "
            "health_safety | other."
        ),
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the risk and its potential impact.",
    )

    # ------------------------------------------------------------------
    # Scoring (1–5 integer scales)
    # ------------------------------------------------------------------
    probability: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Likelihood of the risk occurring: 1 (rare) → 5 (near-certain).",
    )
    impact: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Severity if the risk materialises: 1 (negligible) → 5 (critical).",
    )

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------
    mitigation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Recommended action to reduce or eliminate the risk.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default="open",
        comment="Resolution stage: open | acknowledged | mitigated | closed.",
    )

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------
    report: Mapped["RiskReport"] = relationship(
        "RiskReport",
        back_populates="items",
        lazy="select",
    )
