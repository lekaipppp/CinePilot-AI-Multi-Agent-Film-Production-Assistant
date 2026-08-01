"""
Structured logging configuration for CinePilot AI.

Design decisions
----------------
* Emits **JSON lines** in production (DEBUG=false) for log-aggregation pipelines
  (Supabase Logflare, GCP Cloud Logging, Datadog, etc.).
* Emits a **human-readable coloured format** in development (DEBUG=true).
* Every log record is enriched with a ``request_id`` pulled from a
  ``contextvars.ContextVar`` — middleware sets this per-request so all log
  lines for the same HTTP call share an ID.
* Uvicorn's own loggers are re-configured to use the same handler/formatter
  so the entire process produces a single consistent log stream.
* ``get_logger()`` is the only public API — nothing else in the codebase
  imports ``logging`` directly.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any

# ---------------------------------------------------------------------------
# Per-request correlation ID (set by RequestIDMiddleware in main.py)
# ---------------------------------------------------------------------------
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

class _JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON object on one line."""

    _RESERVED = frozenset(logging.LogRecord(
        "", 0, "", 0, "", (), None
    ).__dict__.keys())

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_ctx.get(),
            "message": message,
        }
        # Attach any extra fields the caller passed (e.g. logger.info("x", extra={"user": 1}))
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                try:
                    json.dumps(value)          # only include JSON-serialisable extras
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


class _DevFormatter(logging.Formatter):
    """Human-readable coloured formatter for local development."""

    _COLOURS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[1;31m", # bold red
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self._COLOURS.get(record.levelname, "")
        rid = request_id_ctx.get()
        rid_part = f" [{rid}]" if rid != "-" else ""
        prefix = (
            f"{colour}{self.formatTime(record, '%H:%M:%S')}"
            f" {record.levelname:<8}{self._RESET}"
            f" {record.name}{rid_part}"
        )
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        return f"{prefix} | {message}"


# ---------------------------------------------------------------------------
# Root handler factory
# ---------------------------------------------------------------------------

def _make_handler(debug: bool) -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_DevFormatter() if debug else _JSONFormatter())
    return handler


# ---------------------------------------------------------------------------
# Public configuration entry-point (called once from main.py lifespan)
# ---------------------------------------------------------------------------

def configure_logging(debug: bool = False, log_level: str = "INFO") -> None:
    """
    Configure the root logger and silence noisy third-party loggers.
    Must be called **before** the FastAPI app processes any request.

    Parameters
    ----------
    debug:
        When True, use the human-readable formatter and set level to DEBUG.
    log_level:
        Minimum log level string (e.g. "INFO", "WARNING").  Overridden to
        "DEBUG" when *debug* is True.
    """
    level = logging.DEBUG if debug else getattr(logging, log_level.upper(), logging.INFO)
    handler = _make_handler(debug)

    # Root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Re-wire uvicorn loggers to our handler so the whole process is consistent
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
        uv_logger.setLevel(level)
        uv_logger.propagate = False

    # Quiet down overly verbose libraries
    for noisy in ("sqlalchemy.engine", "httpx", "httpcore", "google.generativeai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a module-level logger.

    Usage::

        from app.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Project created", extra={"project_id": str(project.id)})
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Uvicorn log_config dict — pass to uvicorn.run() or the CLI via --log-config
# ---------------------------------------------------------------------------

def uvicorn_log_config(debug: bool = False) -> dict:
    """
    Return a uvicorn-compatible ``log_config`` dict that replaces uvicorn's
    default dictConfig with our formatter.
    """
    formatter_class = (
        "app.utils.logging._DevFormatter"
        if debug
        else "app.utils.logging._JSONFormatter"
    )
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": formatter_class,
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "loggers": {
            "uvicorn":        {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error":  {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }
