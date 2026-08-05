from fastapi import APIRputer
from backend.app.api.v1 import screenplay

api_router = APIRputer

api_router.include_router(
    screenplay.router,
    prefix="/screenplay",
    tags=["Screenplay"],
)