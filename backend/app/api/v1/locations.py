from fastapi import APIRouter, HTTPException

from backend.app.agents.location_agent import LocationAgentOutput
from backend.app.schemas.location import LocationSearchRequest
from backend.app.services.location_runner import location_runner
from backend.app.services.parallel_search import search_location_candidates


router = APIRouter()

@router.post(
    "/search",
    response_model=LocationAgentOutput,
)
async def search_locations(
    request: LocationSearchRequest,
) -> LocationAgentOutput:

    scene = request.scene
    requirements = request.user_requirements

    try:
        parallel_results = await search_location_candidates(
            scene=request.scene,
            requirements=request.user_requirements,
        )

        location_result = await location_runner(
            #model_dump is a built-in method that converts a Pydantic model instance into a standard Python dictionary(dict)
            director_analysis=request.scene.model_dump(),

            user_requirements=(
                request.user_requirements.model_dump(mode="json")
            ),
            parallel_results=parallel_results,
            user_id = request.user_id,
        )
        return location_result

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
        raise HTTPException(
            status_code=500,
            detail="Unexpected location pipeline error.",
        ) from error


