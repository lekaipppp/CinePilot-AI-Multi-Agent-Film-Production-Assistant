"""
app/database/database.py
========================
``DatabaseManager`` — a single, application-owned object that encapsulates
every lifecycle concern of the PostgreSQL connection.

All engine access goes through the lazy ``get_engine()`` / ``get_session_factory()``
functions in ``session.py`` — the manager never creates an engine itself and
never crashes at import time.
"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.session import (
    get_connection,
    get_db,
    get_db_context,
    get_engine,
    get_session_factory,
    _is_db_configured,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Façade over SQLAlchemy's async engine and session factory.

    All methods are safe to call only when DATABASE_URL is configured.
    ``ping()`` and ``init_schema()`` raise ``RuntimeError`` with a helpful
    message when the database is not yet set up.
    """

    # ------------------------------------------------------------------
    # Properties — read-only accessors
    # ------------------------------------------------------------------

    @property
    def engine(self):
        """The underlying async SQLAlchemy engine (lazy)."""
        return get_engine()

    @property
    def session_factory(self):
        """The ``async_sessionmaker`` factory bound to the engine (lazy)."""
        return get_session_factory()

    @property
    def is_configured(self) -> bool:
        """True when DATABASE_URL looks like a real connection string."""
        return _is_db_configured()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    async def init_schema(self, *, drop_all: bool = False) -> None:
        """
        Synchronise the database schema with the current ORM models.

        No-ops gracefully when the database is not configured — logs a
        warning instead of crashing so the dev server can start without a DB.
        """
        if not self.is_configured:
            logger.warning(
                "init_schema skipped — DATABASE_URL is not configured. "
                "Set DATABASE_URL in .env to enable automatic schema creation."
            )
            return

        from app.models.base import Base  # noqa: PLC0415

        async with get_engine().begin() as conn:
            if drop_all:
                logger.warning("Dropping all tables — test/dev only!")
                await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        logger.info(
            "Schema initialised",
            extra={"drop_all": drop_all, "env": settings.ENV.value},
        )

    # ------------------------------------------------------------------
    # Health / readiness
    # ------------------------------------------------------------------

    async def ping(self) -> float:
        """
        Issue a ``SELECT 1`` to verify the database is reachable.

        Returns
        -------
        float
            Round-trip latency in milliseconds.

        Raises
        ------
        RuntimeError
            When DATABASE_URL is not configured.
        Exception
            Re-raises any connection / SQL error so the ``/readiness`` probe
            can return HTTP 503.
        """
        start = time.perf_counter()
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.debug("Database ping OK", extra={"latency_ms": latency_ms})
        return latency_ms

    # ------------------------------------------------------------------
    # Pool introspection
    # ------------------------------------------------------------------

    def pool_status(self) -> dict[str, Any]:
        """Return live statistics about the connection pool."""
        if not self.is_configured:
            return {"status": "not_configured"}
        pool = get_engine().pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def dispose(self, *, close: bool = True) -> None:
        """Drain and optionally close all connections in the pool."""
        if not self.is_configured:
            return
        try:
            await get_engine().dispose(close=close)
            logger.info("Database connection pool disposed", extra={"close": close})
        except Exception as exc:
            logger.warning("Error disposing database pool", extra={"error": str(exc)})

    # ------------------------------------------------------------------
    # Session helpers (delegates to session.py)
    # ------------------------------------------------------------------

    def get_session(self) -> AsyncSession:
        """Return an unmanaged ``AsyncSession``."""
        return get_session_factory()()

    get_db = staticmethod(get_db)
    get_db_context = staticmethod(get_db_context)
    get_connection = staticmethod(get_connection)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
db_manager: DatabaseManager = DatabaseManager()
