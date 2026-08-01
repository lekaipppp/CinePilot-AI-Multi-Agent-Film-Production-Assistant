"""
Custom exception hierarchy and FastAPI exception handlers for CinePilot AI.

All handlers return a consistent JSON error envelope:

    {
        "code":       "NOT_FOUND",
        "message":    "Project with id '...' was not found.",
        "request_id": "abc-123",
        "detail":     null          # optional extra context
    }

Registration
------------
Call ``register_exception_handlers(app)`` once in main.py **after** the
FastAPI instance is created but before the app starts receiving requests.
"""

from __future__ import annotations

import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logging import get_logger, request_id_ctx

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class CinePilotBaseError(Exception):
    """Base class for all application-level exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Any = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundError(CinePilotBaseError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id '{resource_id}' was not found.",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(CinePilotBaseError):
    """Raised when an action would violate a uniqueness constraint."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


class UnauthorizedError(CinePilotBaseError):
    """Raised when the caller lacks valid credentials."""

    def __init__(self, message: str = "Authentication required."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(CinePilotBaseError):
    """Raised when the caller lacks permission for the requested action."""

    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class AgentExecutionError(CinePilotBaseError):
    """Raised when a LangGraph agent node fails during execution."""

    def __init__(self, detail: str):
        super().__init__(
            message=f"Agent execution failed: {detail}",
            code="AGENT_EXECUTION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ExternalAPIError(CinePilotBaseError):
    """Raised when a downstream API call (Gemini, Maps, Weather) fails."""

    def __init__(self, service: str, detail: str):
        super().__init__(
            message=f"External API error from '{service}': {detail}",
            code="EXTERNAL_API_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


# ---------------------------------------------------------------------------
# JSON error envelope helper
# ---------------------------------------------------------------------------

def _error_response(
    status_code: int,
    code: str,
    message: str,
    detail: Any = None,
    request_id: str = "-",
) -> JSONResponse:
    body: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


def _get_request_id(request: Request) -> str:
    return request.headers.get("x-request-id", request_id_ctx.get("-"))


# ---------------------------------------------------------------------------
# Individual handlers
# ---------------------------------------------------------------------------

async def _handle_cinepilot_error(
    request: Request, exc: CinePilotBaseError
) -> JSONResponse:
    """Handler for all application-domain exceptions."""
    logger.warning(
        "Application error",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        detail=exc.detail,
        request_id=_get_request_id(request),
    )


async def _handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handler for FastAPI / Starlette HTTP errors (404, 405, etc.)."""
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
        request_id=_get_request_id(request),
    )


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for Pydantic v2 request validation failures.
    Flattens the error list into a human-readable detail array.
    """
    errors = [
        {
            "field": " → ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    logger.info(
        "Request validation failed",
        extra={"path": request.url.path, "errors": errors},
    )
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request validation failed. Check 'detail' for field-level errors.",
        detail=errors,
        request_id=_get_request_id(request),
    )


async def _handle_unhandled_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all handler — logs the full traceback and returns a safe 500.
    Never leaks internal details to the client in production.
    """
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        request_id=_get_request_id(request),
    )


# ---------------------------------------------------------------------------
# Registration helper — called once in main.py
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach all exception handlers to the FastAPI application instance.
    Must be called after the app is created and before it starts.
    """
    app.add_exception_handler(CinePilotBaseError, _handle_cinepilot_error)          # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)        # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)      # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unhandled_exception)                # type: ignore[arg-type]
