import logging

from fastapi import APIRouter, HTTPException

from backend.app.schemas.report import (
    ReportAgentOutput,
    ReportGenerateRequest,
)
from backend.app.services.report_runner import report_runner

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=ReportAgentOutput,
)
async def generate_report(
    request: ReportGenerateRequest,
) -> ReportAgentOutput:

    try:
        return await report_runner(
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
            risk=(
                request.risk.model_dump(mode="json")
                if request.risk is not None
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
        logger.exception("Unexpected report pipeline error")

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected report pipeline error: {error}",
        ) from error
