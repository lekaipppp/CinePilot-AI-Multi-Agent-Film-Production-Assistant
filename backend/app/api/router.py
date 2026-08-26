from fastapi import APIRouter

from backend.app.api.v1 import auth, locations, screenplay


api_router = APIRouter()


api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

api_router.include_router(
    screenplay.router,
    prefix="/screenplay",
    tags=["Screenplay"],
)

api_router.include_router(
    locations.router,
    prefix="/locations",
    tags=["Locations"],
)