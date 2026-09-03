import logging

from fastapi import APIRouter, HTTPException

from backend.app.schemas.budget import (
    BudgetAgentOutput,
    BudgetGenerateRequest,
)
from backend.app.services.budget_runner import budget_runner

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=BudgetAgentOutput,
)
async def generate_budget(
    request: BudgetGenerateRequest,
) -> BudgetAgentOutput:

    try:
        return await budget_runner(
            scenes=[scene.model_dump() for scene in request.scenes],
            selected_locations=[
                location.model_dump(mode="json")
                for location in request.selected_locations
            ],
            total_shoot_days=request.total_shoot_days,
            constraints=request.constraints.model_dump(mode="json"),
            user_id=request.user_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Unexpected budget pipeline error")

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected budget pipeline error: {error}",
        ) from error
