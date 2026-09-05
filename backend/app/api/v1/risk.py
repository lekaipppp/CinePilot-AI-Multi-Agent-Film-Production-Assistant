import logging

from fastapi import APIRouter, HTTPException

from backend.app.schemas.risk import (
    RiskAgentOutput,
    RiskGenerateRequest,
)
from backend.app.services.risk_runner import risk_runner

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=RiskAgentOutput,
)
async def generate_risk(
    request: RiskGenerateRequest,
) -> RiskAgentOutput:

    try:
        return await risk_runner(
            scenes=[scene.model_dump() for scene in request.scenes],
            selected_locations=[
                location.model_dump(mode="json")
                for location in request.selected_locations
            ],
            schedule=(
                request.schedule.model_dump(mode="json")
                if request.schedule is not None
                else None
            ),
            budget=(
                request.budget.model_dump(mode="json")
                if request.budget is not None
                else None
            ),
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
        logger.exception("Unexpected risk pipeline error")

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected risk pipeline error: {error}",
        ) from error
