import logging

from fastapi import APIRouter, HTTPException

from backend.app.schemas.scheduler import (
    SchedulerAgentOutput,
    SchedulerGenerateRequest,
)
from backend.app.services.scheduler_runner import scheduler_runner

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=SchedulerAgentOutput,
)
async def generate_schedule(
    request: SchedulerGenerateRequest,
) -> SchedulerAgentOutput:

    try:
        return await scheduler_runner(
            scenes=[scene.model_dump() for scene in request.scenes],
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
        logger.exception("Unexpected scheduler pipeline error")

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected scheduler pipeline error: {error}",
        ) from error
