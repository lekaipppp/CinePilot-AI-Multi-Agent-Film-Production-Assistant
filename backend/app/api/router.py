from fastapi import APIRouter
from backend.app.api.v1 import screenplay

api_router = APIRouter()

api_router.include_router(
    screenplay.router,
    prefix="/screenplay",
    tags=["Screenplay"],
)