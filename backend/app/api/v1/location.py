from fastapi import APIRouter

from backend.app.schemas.location import (
    LocationRequestConfirmation,
    LocationSearchRequest,
)

router = APIRouter()

@router.post(
    "/search",
    response_model=LocationRequestConfirmation,
)
async def search_locations(
    request: LocationSearchRequest,
) -> LocationRequestConfirmation:

    scene = request.scene
    requirements = request.user_requirements

    print("\nDirector Agent scene received:")
    print(scene.model_dump_json(indent=2))

    print("\nUser location requirements received:")
    print(requirements.model_dump_json(indent=2))

    return LocationRequestConfirmation(
        status="received",
        scene_number=scene.scene_number,
        preferred_region=requirements.preferred_region,
        message=(
            "Received the Director Agent analysis and location "
            f"requirements for Scene {scene.scene_number}."
        ),
    )