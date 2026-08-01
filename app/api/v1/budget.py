"""
app/api/v1/budget.py
====================
Budget router – manage the production budget for a project.

Routes
------
GET  /budget/{project_id}    Retrieve the current budget (with line items).
POST /budget/update          Create or replace the budget for a project.

All business logic is delegated to BudgetService via the deps.py dependency.
"""

import uuid

from fastapi import APIRouter, Depends, status

from app.deps import get_budget_service
from app.schemas.budget import BudgetRead, BudgetUpdateRequest
from app.services.budget_service import BudgetService

router = APIRouter()


@router.get(
    "/{project_id}",
    response_model=BudgetRead,
    summary="Get budget for a project",
    description=(
        "Returns the production budget and all line items for the given project. "
        "Returns 404 if the pipeline has not been run yet."
    ),
)
async def get_budget(
    project_id: uuid.UUID,
    svc: BudgetService = Depends(get_budget_service),
) -> BudgetRead:
    """Fetch the Budget row with its items for the given project."""
    return await svc.get_by_project(project_id)


@router.post(
    "/update",
    response_model=BudgetRead,
    status_code=status.HTTP_200_OK,
    summary="Create or update the budget for a project",
    description=(
        "Creates a new budget if none exists, or updates the existing one. "
        "When ``items`` is provided in the request body, all current line items "
        "are replaced and ``total_estimated_cost`` is recomputed automatically. "
        "Omit ``items`` to update only scalar fields (currency, status, etc.)."
    ),
)
async def update_budget(
    payload: BudgetUpdateRequest,
    svc: BudgetService = Depends(get_budget_service),
) -> BudgetRead:
    """Upsert a project's budget and optionally replace all line items."""
    return await svc.upsert(payload)
