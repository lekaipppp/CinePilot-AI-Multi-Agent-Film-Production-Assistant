"""
Top-level API router that wires all versioned sub-routers together.
Adding a new domain router requires only one import + include here.
"""

from fastapi import APIRouter

from app.api.v1 import agents, budget, pipeline, projects, scenes, schedule, script

api_router = APIRouter()

# Core project CRUD
api_router.include_router(projects.router, prefix="/projects",  tags=["Projects"])
api_router.include_router(scenes.router,   prefix="/projects",  tags=["Scenes"])

# Script management
api_router.include_router(script.router,   prefix="/script",    tags=["Script"])

# Multi-agent pipeline
api_router.include_router(pipeline.router, prefix="/pipeline",  tags=["Pipeline"])

# AI agent sessions (existing stubs)
api_router.include_router(agents.router,   prefix="/agents",    tags=["Agents"])

# Production plan results
api_router.include_router(budget.router,   prefix="/budget",    tags=["Budget"])
api_router.include_router(schedule.router, prefix="/schedule",  tags=["Schedule"])
