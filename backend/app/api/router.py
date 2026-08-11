from fastapi import APIRouter
from backend.app.api.v1 import screenplay
from backend.app.api.v1 import location
api_router = APIRouter()

api_router.include_router(
    screenplay.router,
    prefix="/screenplay",
    tags=["Screenplay"],
)


api_router.include_router(
    location.router,
    prefix="/location",
    tags=["Locations"],
)