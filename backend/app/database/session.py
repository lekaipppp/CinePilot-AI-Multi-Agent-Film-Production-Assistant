"""
app/database/session.py
=======================
Async SQLAlchemy engine and scoped session factory.

Design notes
------------
* The engine is built **lazily** — only when first accessed — so importing
  this module at startup never crashes if DATABASE_URL is a placeholder or
  not yet set.  The engine is created the first time ``get_engine()`` is
  called, which happens only inside ``get_db()`` or when the lifespan hook
  explicitly warms the pool.

* SSL is enabled by default for Supabase connections.  Set DB_SSL_REQUIRED=false
  only when connecting to a local plain-text instance.

* ``get_db()`` is a FastAPI ``Depends``-compatible async generator that:
  - Opens a session from the pool.
  - Commits on clean exit.
  - Rolls back and re-raises on any exception.
  - Always closes the session, returning it to the pool.

* ``get_db_context()`` is a plain async context-manager for use outside of
  FastAPI route handlers (e.g. background tasks, CLI scripts, tests).
"""

from __future__ import annotations

import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# SSL context for Supabase
# ---------------------------------------------------------------------------

def _build_ssl_context() -> ssl.SSLContext | bool:
    """
    Return an SSL context suitable for Supabase's managed PostgreSQL.
    Returns False if SSL is disabled in settings.
    """
    if not settings.DB_SSL_REQUIRED:
        return False

    ctx = ssl.create_default_context()
    return ctx


# ---------------------------------------------------------------------------
# Lazy engine — built on first access, never at import time
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


def _is_db_configured() -> bool:
    """
    Return True if DATABASE_URL looks like a real connection string.
    Placeholder values (the default in settings) are detected and treated
    as "not configured" so the app boots cleanly without a DB.
    """
    url = settings.DATABASE_URL
    placeholder_indicators = (
        "user:password@localhost",
        "USER:PASSWORD@HOST",
        "localhost:5432/cinepilot",
    )
    return not any(p in url for p in placeholder_indicators)


def get_engine() -> AsyncEngine:
    """
    Return (or lazily create) the module-level async engine singleton.

    Raises
    ------
    RuntimeError
        When DATABASE_URL has not been configured yet — gives a clear
        human-readable error instead of an asyncpg connection failure.
    """
    global _engine, _session_factory

    if _engine is not None:
        return _engine

    if not _is_db_configured():
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Copy .env.example to .env and set a valid PostgreSQL connection string. "
            "See README.md → Setup → Step 2."
        )

    connect_args: dict = {}
    ssl_ctx = _build_ssl_context()
    if ssl_ctx:
        connect_args["ssl"] = ssl_ctx

    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        echo_pool=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        connect_args=connect_args,
        query_cache_size=1200,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    logger.info(
        "Database engine created",
        extra={
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "ssl": settings.DB_SSL_REQUIRED,
        },
    )
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Return (or lazily create) the async session factory."""
    global _session_factory
    if _session_factory is None:
        get_engine()  # creates both _engine and _session_factory
    return _session_factory  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Backward-compatible module-level aliases
# These are properties on a proxy object so legacy code that does
#   from app.database.session import engine
# still works — it just gets the lazy accessor.
# ---------------------------------------------------------------------------

class _EngineProxy:
    """
    Proxy that resolves the lazy engine/session-factory on attribute access.
    Allows ``from app.database.session import engine, AsyncSessionFactory``
    to keep working without triggering engine creation at import time.
    """

    def __getattr__(self, name: str):
        if name == "engine":
            return get_engine()
        if name in ("AsyncSessionFactory", "session_factory"):
            return get_session_factory()
        raise AttributeError(name)


_proxy = _EngineProxy()


# These names are imported by other modules.  They resolve lazily through
# the proxy so they never crash at import time.
class _LazyEngineDescriptor:
    """Descriptor that returns the lazy engine when the module attr is accessed."""
    def __get__(self, obj, objtype=None):
        return get_engine()


# Provide direct importable names as module-level callables/lazily-resolved
# We expose them through functions so callers who do
#   from app.database.session import engine
# get a reference that will work after the engine is initialised.
# The actual singletons live in the _engine/_session_factory globals.

def _get_engine_compat():
    return get_engine()

def _get_factory_compat():
    return get_session_factory()


# Module-level names — these are *functions* now, not the objects themselves.
# All internal consumers in this codebase use get_engine() or get_session_factory().
# For backward compat with any code doing `engine.connect()` directly we expose
# a thin proxy object whose methods forward to get_engine().
class _EngineShim:
    """
    Shim that forwards all attribute access to the lazily-created engine.
    Assign to the module-level ``engine`` name so code doing
        from app.database.session import engine
        await engine.connect()
    works transparently.
    """
    def __getattr__(self, item):
        return getattr(get_engine(), item)

    def __repr__(self):
        return f"<EngineShim wrapping {get_engine()!r}>"


class _SessionFactoryShim:
    """Shim for the async_sessionmaker, forwards all calls to the lazy factory."""
    def __call__(self, *args, **kwargs):
        return get_session_factory()(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(get_session_factory(), item)


# Module-level singletons — NOW LAZY (no DB call at import time)
engine: AsyncEngine = _EngineShim()                     # type: ignore[assignment]
AsyncSessionFactory = _SessionFactoryShim()              # type: ignore[assignment]


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI ``Depends``-compatible async session dependency.

    Raises RuntimeError (→ HTTP 503) when DATABASE_URL is not configured.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Context-manager variant (for use outside FastAPI route handlers)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def get_db_context() -> AsyncIterator[AsyncSession]:
    """
    Async context manager that yields a database session.
    Same commit/rollback/close semantics as ``get_db()``.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Connection-level accessor (for DDL / raw SQL / Alembic)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def get_connection() -> AsyncIterator[AsyncConnection]:
    """
    Yield a raw ``AsyncConnection`` from the engine pool.
    Intended for DDL statements, bulk operations, and Alembic migrations.
    """
    eng = get_engine()
    async with eng.connect() as conn:
        yield conn
