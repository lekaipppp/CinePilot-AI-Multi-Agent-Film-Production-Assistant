from fastapi import APIRouter

from backend.app.api.v1 import budget, locations, scheduler, screenplay
# from backend.app.api.v1 import auth  # 暂时禁用：auth.py 依赖的 app.database / app.models 还没写


api_router = APIRouter()

# api_router.include_router(
#     auth.router,
#     prefix="/auth",
#     tags=["Auth"],
# )

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

api_router.include_router(
    scheduler.router,
    prefix="/scheduler",
    tags=["Scheduler"],
)

api_router.include_router(
    budget.router,
    prefix="/budget",
    tags=["Budget"],
)