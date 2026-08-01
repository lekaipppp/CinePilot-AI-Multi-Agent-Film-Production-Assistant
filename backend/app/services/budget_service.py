"""
app/services/budget_service.py
===============================
BudgetService – manages Budget and BudgetItem records for a Project.

Responsibility
--------------
* ``get_by_project``   — fetch the Budget (with items) for a given project.
* ``upsert``           — create or fully replace a budget with new line items.
  When ``items`` are provided the existing BudgetItem rows are deleted and
  re-created so the UI always sees a consistent set (no orphaned items).
  ``total_estimated_cost`` is recomputed from the provided items on every write.

All writes use ``session.flush()`` — ``get_db()`` owns the commit.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.budget import Budget, BudgetItem
from app.schemas.budget import BudgetUpdateRequest
from app.services.project_service import ProjectService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class BudgetService:
    """Handles persistence of Budget and BudgetItem entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._project_svc = ProjectService(db)

    async def get_by_project(self, project_id: uuid.UUID) -> Budget:
        """
        Return the Budget row (with its items) for the given project.

        Parameters
        ----------
        project_id:
            UUID of the project whose budget to retrieve.

        Returns
        -------
        Budget
            The Budget ORM instance with ``items`` eagerly loaded.

        Raises
        ------
        HTTPException 404
            When the project does not exist or has no budget yet.
        """
        # Confirm the project exists first (raises 404 if not)
        await self._project_svc.get_or_404(project_id)

        result = await self.db.execute(
            select(Budget)
            .where(Budget.project_id == project_id)
            .options(selectinload(Budget.items))
        )
        budget = result.scalar_one_or_none()
        if budget is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No budget found for project {project_id}. Run the pipeline first.",
            )
        return budget

    async def upsert(self, payload: BudgetUpdateRequest) -> Budget:
        """
        Create or fully replace the budget for a project.

        If a Budget row already exists for ``payload.project_id``, its scalar
        fields are updated.  If ``payload.items`` is provided, all existing
        BudgetItem rows are deleted and replaced with the new list.
        ``total_estimated_cost`` is recomputed automatically.

        Parameters
        ----------
        payload:
            Validated ``BudgetUpdateRequest`` schema.

        Returns
        -------
        Budget
            The created / updated Budget instance with items loaded.

        Raises
        ------
        HTTPException 404
            When the project does not exist.
        """
        # Validate project exists
        await self._project_svc.get_or_404(payload.project_id)

        # Load existing budget (if any) with items
        result = await self.db.execute(
            select(Budget)
            .where(Budget.project_id == payload.project_id)
            .options(selectinload(Budget.items))
        )
        budget = result.scalar_one_or_none()

        if budget is None:
            # Create fresh budget row
            budget = Budget(
                project_id=payload.project_id,
                currency=payload.currency or "USD",
                contingency_pct=payload.contingency_pct,
                assumptions=payload.assumptions,
                status=payload.status or "draft",
            )
            self.db.add(budget)
            await self.db.flush()        # obtain budget.id for FKs below
            await self.db.refresh(budget)
        else:
            # Apply scalar-field patches (only non-None values)
            if payload.currency is not None:
                budget.currency = payload.currency
            if payload.contingency_pct is not None:
                budget.contingency_pct = payload.contingency_pct
            if payload.assumptions is not None:
                budget.assumptions = payload.assumptions
            if payload.status is not None:
                budget.status = payload.status

        # Replace items when provided
        if payload.items is not None:
            # Delete existing items
            for item in list(budget.items):
                await self.db.delete(item)
            await self.db.flush()

            # Insert replacement items
            new_items: List[BudgetItem] = []
            for item_data in payload.items:
                item = BudgetItem(
                    budget_id=budget.id,
                    category=item_data.category,
                    label=item_data.label,
                    amount=item_data.amount,
                    notes=item_data.notes,
                )
                self.db.add(item)
                new_items.append(item)

            await self.db.flush()

            # Recompute total from new items
            budget.total_estimated_cost = sum(i.amount for i in new_items)
            await self.db.flush()

        await self.db.refresh(budget)

        # Reload items relationship after mutations
        result2 = await self.db.execute(
            select(Budget)
            .where(Budget.id == budget.id)
            .options(selectinload(Budget.items))
        )
        return result2.scalar_one()
