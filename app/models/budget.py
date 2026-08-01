"""
app/models/budget.py
====================
ORM models for the ``budgets`` and ``budget_items`` tables.

A Budget is the AI-generated production cost estimate for a Project.
It is broken down into BudgetItem rows, each representing a single
department or cost category.

Design decisions
----------------
``Budget`` (one-to-one with Project)
    Stores the currency, total estimated cost, and a contingency percentage.
    ``total_estimated_cost`` is a denormalised sum of all BudgetItem amounts —
    recomputed by the application whenever items change so the report endpoint
    never needs a SUM() query.
    ``contingency_pct`` stores the percentage as a plain FLOAT (e.g. 15.0 for
    15%) rather than a fraction to make the value human-readable in the DB.

``BudgetItem`` (one-to-many with Budget)
    One row per cost category / department.
    ``category`` is a validated VARCHAR with a CHECK constraint.
    ``amount`` is NUMERIC(12,2): 10 digits before the decimal, 2 after —
    supports budgets up to $9,999,999,999.99 without floating-point rounding.
    ``notes`` carries agent rationale or production notes per line item.

Why NUMERIC not FLOAT for money
    IEEE 754 FLOAT is imprecise for currency arithmetic (0.1 + 0.2 ≠ 0.3).
    PostgreSQL NUMERIC stores exact decimal values.

Indexes
-------
* ``ix_budgets_project_id``       — look up a project's budget.
* ``ix_budget_items_budget_id``   — all line items for a budget.
* ``ix_budget_items_category``    — filter/group by department.

Relationships
-------------
``Budget.project``       → one-to-one   Project (back)
``Budget.items``         → one-to-many  BudgetItem (cascade delete)
``BudgetItem.budget``    → many-to-one  Budget
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class Budget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    The AI-generated production budget for a project.

    One budget per project (one-to-one enforced at DB level by ``unique=True``
    on ``project_id``).
    """

    __tablename__ = "budgets"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','approved','revised','locked')",
            name="ck_budgets_status",
        ),
        CheckConstraint(
            "contingency_pct IS NULL OR (contingency_pct >= 0 AND contingency_pct <= 100)",
            name="ck_budgets_contingency_pct",
        ),
        Index("ix_budgets_project_id", "project_id"),
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,        # one budget per project
        comment="Owning project (unique — one budget per project).",
    )

    # ------------------------------------------------------------------
    # Financial metadata
    # ------------------------------------------------------------------
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default="USD",
        comment="ISO 4217 currency code (e.g. 'USD', 'EUR', 'GBP').",
    )
    total_estimated_cost: Mapped[float | None] = mapped_column(
        Numeric(precision=14, scale=2),
        nullable=True,
        comment=(
            "Denormalised sum of all BudgetItem amounts.  "
            "Updated by the application layer whenever items change."
        ),
    )
    contingency_pct: Mapped[float | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
        comment="Contingency reserve as a percentage of total (e.g. 15.00 = 15%).",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
        comment="Budget stage: draft | approved | revised | locked.",
    )
    assumptions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Agent-generated assumptions behind the cost estimates.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="budget",
        lazy="select",
    )
    items: Mapped[list["BudgetItem"]] = relationship(
        "BudgetItem",
        back_populates="budget",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="BudgetItem.category",
        doc="Individual cost line items, ordered by category name.",
    )


# ---------------------------------------------------------------------------
# BudgetItem
# ---------------------------------------------------------------------------

class BudgetItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single line item in a production budget.

    Each item maps to one cost category (department).
    """

    __tablename__ = "budget_items"

    __table_args__ = (
        CheckConstraint(
            "category IN ("
            "'above_the_line','below_the_line','production',"
            "'post_production','equipment','locations',"
            "'cast','crew','other'"
            ")",
            name="ck_budget_items_category",
        ),
        CheckConstraint(
            "amount >= 0",
            name="ck_budget_items_amount_non_negative",
        ),
        Index("ix_budget_items_budget_id", "budget_id"),
        Index("ix_budget_items_category",  "category"),
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent budget.",
    )

    # ------------------------------------------------------------------
    # Line-item detail
    # ------------------------------------------------------------------
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment=(
            "Cost category / department: above_the_line | below_the_line | "
            "production | post_production | equipment | locations | "
            "cast | crew | other."
        ),
    )
    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable label for this line item (e.g. 'Director Fee').",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        default=0,
        comment="Estimated cost in the budget's currency (non-negative).",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Agent rationale or production notes for this estimate.",
    )

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------
    budget: Mapped["Budget"] = relationship(
        "Budget",
        back_populates="items",
        lazy="select",
    )
