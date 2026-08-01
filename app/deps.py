"""
Shared FastAPI dependency callables.
Import these in routers instead of duplicating dependency construction.
All service classes receive the async DB session via DI — never instantiate
them inline in route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.agent_session_service import AgentSessionService
from app.services.budget_service import BudgetService
from app.services.gemini_service import GeminiService
from app.services.location_service import LocationService
from app.services.pipeline_service import PipelineService
from app.services.project_service import ProjectService
from app.services.schedule_service import ScheduleService
from app.services.script_service import ScriptService


# --------------------------------------------------------------------------- #
# Database-backed services                                                      #
# --------------------------------------------------------------------------- #

def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


def get_agent_session_service(db: AsyncSession = Depends(get_db)) -> AgentSessionService:
    return AgentSessionService(db)


def get_script_service(db: AsyncSession = Depends(get_db)) -> ScriptService:
    return ScriptService(db)


def get_pipeline_service(db: AsyncSession = Depends(get_db)) -> PipelineService:
    return PipelineService(db)


def get_budget_service(db: AsyncSession = Depends(get_db)) -> BudgetService:
    return BudgetService(db)


def get_schedule_service(db: AsyncSession = Depends(get_db)) -> ScheduleService:
    return ScheduleService(db)


# --------------------------------------------------------------------------- #
# Stateless / singleton services (no DB session required)                      #
# --------------------------------------------------------------------------- #

def get_gemini_service() -> GeminiService:
    return GeminiService()


def get_location_service() -> LocationService:
    return LocationService()
