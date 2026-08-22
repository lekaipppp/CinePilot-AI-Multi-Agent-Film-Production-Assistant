from fastapi import APIRouter
<<<<<<< HEAD
from backend.app.api.v1 import screenplay
from backend.app.api.v1 import locations
api_router = APIRouter()

=======

from app.api.v1 import (
    agents,
    auth,
    budget,
    pipeline,
    projects,
    scenes,
    schedule,
    screenplay,
    script,
)


api_router = APIRouter()


# Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)


# Core project CRUD
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["Projects"],
)

api_router.include_router(
    scenes.router,
    prefix="/projects",
    tags=["Scenes"],
)


# Script storage and retrieval
api_router.include_router(
    script.router,
    prefix="/script",
    tags=["Script"],
)


# Director Agent screenplay analysis
# screenplay.py already provides the "/screenplay" prefix,
# so we do not add another prefix here.
>>>>>>> dbb9f72 (Added authentication page)
api_router.include_router(
    screenplay.router,
    prefix="/screenplay",
    tags=["Screenplay"],
)


api_router.include_router(
    locations.router,
    prefix="/locations",
    tags=["Locations"],
)from fastapi import APIRouter
from backend.app.api.v1 import screenplay
from backend.app.api.v1 import locations
from backend.app.api.v1 import auth

api_router = APIRouter()

# Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

# Screenplay
api_router.include_router(
    screenplay.router,
    prefix="/screenplay",
    tags=["Screenplay"],
)

# Locations
api_router.include_router(
    locations.router,
    prefix="/locations",
    tags=["Locations"],
)