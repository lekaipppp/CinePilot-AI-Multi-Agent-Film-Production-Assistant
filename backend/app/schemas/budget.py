"""
app/schemas/budget.py
=====================
Pydantic schemas for Budget and BudgetItem endpoints.

Mirrors the ORM models (app/models/budget.py) without exposing internal
foreign keys or SQLAlchemy internals.

Budget categories must match the CHECK constraint in the ORM model:
    above_the_line | below_the_line | production | post_production
    equipment | locations | cast | crew | other
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

BudgetCategory = Literal[
    "above_the_line",
    "below_the_line",
    "production",
    "post_production",
    "equipment",
    "locations",
    "cast",
    "crew",
    "other",
]

BudgetStatus = Literal["draft", "approved", "revised", "locked"]


# --------------------------------------------------------------------------- #
# BudgetItem schemas                                                            #
# --------------------------------------------------------------------------- #

class BudgetItemBase(BaseModel):
    category: BudgetCategory
    label: str = Field(..., max_length=255)
    amount: float = Field(..., ge=0, description="Estimated cost (non-negative).")
    notes: Optional[str] = None


class BudgetItemCreate(BudgetItemBase):
    """Used when adding a single line item via the update endpoint."""
    pass


class BudgetItemRead(BudgetItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    budget_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Budget schemas                                                                #
# --------------------------------------------------------------------------- #

class BudgetUpdateRequest(BaseModel):
    """
    Payload for ``POST /budget/update``.

    Replaces all existing BudgetItem rows with the provided ``items`` list
    and recomputes ``total_estimated_cost``.  Any field left as ``None`` is
    not changed (PATCH semantics for scalar fields).
    """
    project_id: uuid.UUID = Field(
        ...,
        description="UUID of the project whose budget is being updated.",
    )
    currency: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code (e.g. 'USD').",
    )
    contingency_pct: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Contingency reserve percentage (0–100).",
    )
    assumptions: Optional[str] = None
    status: Optional[BudgetStatus] = None
    items: Optional[List[BudgetItemCreate]] = Field(
        default=None,
        description=(
            "Full replacement list of budget line items.  "
            "When provided, all existing items are deleted and replaced."
        ),
    )


class BudgetRead(BaseModel):
    """Full budget representation returned to the client."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    currency: str
    total_estimated_cost: Optional[float] = None
    contingency_pct: Optional[float] = None
    status: str
    assumptions: Optional[str] = None
    items: List[BudgetItemRead] = []
    created_at: datetime
    updated_at: datetime
