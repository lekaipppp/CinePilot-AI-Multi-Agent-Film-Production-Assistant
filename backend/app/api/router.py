"""
Top-level API router that wires all versioned sub-routers together.
Adding a new domain router requires one import and one include here.
"""

from fastapi import APIRouter

from app.api.v1 import (
    agents,
    budget,
    pipeline,
    projects,
    scenes,
    schedule,
    screenplay,
    script,
)


api_router = APIRouter()


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
api_router.include_router(
    screenplay.router,
)


# Multi-agent pipeline
api_router.include_router(
    pipeline.router,
    prefix="/pipeline",
    tags=["Pipeline"],
)


# AI agent sessions
api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["Agents"],
)


# Production plan results
api_router.include_router(
    budget.router,
    prefix="/budget",
    tags=["Budget"],
)

api_router.include_router(
    schedule.router,
    prefix="/schedule",
    tags=["Schedule"],
)