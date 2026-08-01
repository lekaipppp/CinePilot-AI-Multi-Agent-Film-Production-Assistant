"""
CinePilot AI – FastAPI Application Entry Point
===============================================

Startup is designed to be fault-tolerant:
- Missing DATABASE_URL → server boots, /health works, DB endpoints return 503.
- Missing API keys     → server boots, key-gated endpoints return 503 at call time.
- All probes (/health, /readiness, /docs) always work regardless of external services.

Running
-------
Development:
    uvicorn app.main:app --reload --port 8000

Production:
    gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ── Step 1: configure logging before anything else can emit log records ──────
from app.config.settings import settings
from app.utils.logging import configure_logging, get_logger, request_id_ctx

configure_logging(debug=settings.DEBUG, log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# ── Remaining imports ─────────────────────────────────────────────────────────
from app.api.router import api_router
from app.database.database import db_manager
from app.exceptions import register_exception_handlers
import app.models  # noqa: F401 – registers all ORM models with Base.metadata


# ---------------------------------------------------------------------------
# Middleware: request ID + access log
# ---------------------------------------------------------------------------

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attaches a correlation ID to every request via x-request-id header."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)

        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            request_id_ctx.reset(token)

        response.headers["x-request-id"] = request_id

        logger.info(
            "HTTP request",
            extra={
                "method":      request.method,
                "path":        request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id":  request_id,
                "client":      request.client.host if request.client else "unknown",
            },
        )
        return response


# ---------------------------------------------------------------------------
# Lifespan: startup and shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Startup / shutdown lifecycle.

    Database connectivity is attempted but failures are non-fatal:
    the server starts regardless.  A warning is logged so the operator
    knows configuration is incomplete.
    """
    logger.info(
        "Starting CinePilot AI",
        extra={
            "version":      settings.APP_VERSION,
            "environment":  settings.ENV.value,
            "debug":        settings.DEBUG,
            "log_level":    settings.LOG_LEVEL,
            "docs_enabled": settings.DOCS_ENABLED,
        },
    )

    # ── Database warm-up (optional — skipped when DB is not configured) ───
    if not db_manager.is_configured:
        logger.warning(
            "DATABASE_URL is not configured — skipping database warm-up. "
            "Set DATABASE_URL in .env to enable database features."
        )
    else:
        try:
            if settings.is_development:
                # Auto-create tables in dev so engineers can run without Alembic
                await db_manager.init_schema()
            else:
                # In staging/production probe connectivity; Alembic owns schema
                latency_ms = await db_manager.ping()
                logger.info(
                    "Database connectivity verified",
                    extra={"latency_ms": latency_ms},
                )
        except Exception as exc:
            # Log but do NOT crash — the server starts without a DB connection.
            # Endpoints that require the DB will return 503 at call time.
            logger.error(
                "Database warm-up failed — server starting without database. "
                "Check DATABASE_URL and network connectivity.",
                extra={"error": str(exc)},
            )

    yield  # ── Application runs here ──────────────────────────────────────

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down CinePilot AI — disposing database pool")
    await db_manager.dispose()
    logger.info("Shutdown complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application.

    Keeping this in a factory function makes the app easy to instantiate
    in tests with different settings.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered multi-agent assistant for film production planning. "
            "Powered by Google Gemini, LangGraph, Google Maps, and OpenWeather."
        ),
        version=settings.APP_VERSION,
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=lifespan,
    )

    # ── Exception handlers ────────────────────────────────────────────────
    register_exception_handlers(application)

    # ── Middleware ────────────────────────────────────────────────────────
    # Registered in reverse (last = outermost wrapper):
    application.add_middleware(GZipMiddleware, minimum_size=1024)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=["x-request-id"],
    )
    if not settings.is_development:
        application.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.TRUSTED_HOSTS,
        )
    application.add_middleware(RequestIDMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # ── Probes ────────────────────────────────────────────────────────────
    _register_probes(application)

    return application


# ---------------------------------------------------------------------------
# Health / readiness probes
# ---------------------------------------------------------------------------

def _register_probes(app: FastAPI) -> None:
    """Register /health and /readiness outside the versioned API prefix."""

    @app.get(
        "/health",
        tags=["Observability"],
        summary="Liveness probe — is the process alive?",
        include_in_schema=True,
    )
    async def health() -> dict:
        """
        Always returns HTTP 200 as long as the process is running.
        No external dependencies are checked here.
        """
        return {
            "status":      "ok",
            "service":     settings.APP_NAME,
            "version":     settings.APP_VERSION,
            "environment": settings.ENV.value,
        }

    @app.get(
        "/readiness",
        tags=["Observability"],
        summary="Readiness probe — is the service ready to serve traffic?",
        include_in_schema=True,
    )
    async def readiness() -> dict:
        """
        Checks database connectivity.

        Returns HTTP 200 even when the database is not configured — the
        response body will explain the configuration state so this never
        blocks container orchestrators during local development.
        """
        if not db_manager.is_configured:
            # Not a failure — just not set up yet
            return {
                "status":  "degraded",
                "service": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "checks": {
                    "database": {
                        "status":  "not_configured",
                        "message": (
                            "DATABASE_URL is not set. "
                            "Copy .env.example to .env and add your Supabase URL."
                        ),
                    }
                },
            }

        try:
            latency_ms = await db_manager.ping()
            db_check: dict = {"status": "ok", "latency_ms": latency_ms}
            overall = "ready"
        except Exception as exc:
            logger.error(
                "Readiness check: database unreachable",
                extra={"error": str(exc)},
            )
            db_check = {"status": "error", "message": str(exc)}
            overall = "degraded"

        return {
            "status":  overall,
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "checks":  {"database": db_check},
        }


# ---------------------------------------------------------------------------
# Module-level app instance — uvicorn target: ``app.main:app``
# ---------------------------------------------------------------------------
app: FastAPI = create_app()
