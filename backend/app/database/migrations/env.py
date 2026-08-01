"""
app/database/migrations/env.py
==============================
Alembic migration environment.

This file is invoked by Alembic for every ``alembic`` CLI command.
It has two execution modes:

``run_migrations_offline()``
    Generates SQL scripts without a live database connection.
    Useful for reviewing or applying migrations manually.

``run_migrations_online()``
    Applies migrations against a live database using an async connection.
    This is the default mode used by ``alembic upgrade head``.

Async support
-------------
SQLAlchemy 2 + asyncpg requires that Alembic migrations run over a
*synchronous* connection even when the rest of the app uses asyncio.
The pattern recommended by the SQLAlchemy docs is:

    1. Create a standard (sync) engine from the same DATABASE_URL but
       using the ``psycopg2`` driver.
    2. Run Alembic's ``run_migrations_online()`` synchronously via that engine.

Alternatively (the approach used here), we use
``asyncio.run()`` + ``connectable.run_sync()`` to drive migrations through
the existing async engine — no extra driver needed.

See: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# ── Load application settings ────────────────────────────────────────────────
# Import settings before anything else so DATABASE_URL is available.
from app.config.settings import settings

# ── Import all models so Base.metadata includes every table ──────────────────
import app.models  # noqa: F401 – registers Project, Scene, AgentSession
from app.models.base import Base

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Configure Python logging from alembic.ini if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object Alembic uses for --autogenerate
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations by emitting SQL to stdout (no live DB connection needed).

    Useful for:
    * Generating a ``.sql`` file to review before applying.
    * Applying migrations in environments where direct DB access is restricted.
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Emit `CREATE SCHEMA IF NOT EXISTS` when using Supabase schemas
        include_schemas=True,
        # Compare server defaults so Alembic detects changes to column defaults
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode (async)
# ---------------------------------------------------------------------------

def do_run_migrations(connection) -> None:
    """Called synchronously inside ``run_sync()`` with a raw DBAPI connection."""
    # Filter objects so only application tables/indexes/constraints in the
    # `public` schema are considered by autogenerate. This prevents Alembic
    # from touching Supabase-managed schemas such as `auth`, `storage`, and
    # `realtime` during `alembic revision --autogenerate` or `alembic upgrade`.
    IGNORED_SCHEMAS = {
        "auth",
        "storage",
        "realtime",
        "extensions",
        "pg_catalog",
        "information_schema",
    }

    def _get_schema(obj, compare_to):
        if obj is not None:
            schema = getattr(obj, "schema", None)
            if schema:
                return schema
        if compare_to is not None:
            return getattr(compare_to, "schema", None)
        return None

    def include_object(object_, name, type_, reflected, compare_to):
        # Only include objects that live in the `public` schema (or have
        # no explicit schema). Exclude everything in Supabase/PG system
        # schemas to avoid accidental DROP/ALTER operations.
        schema = _get_schema(object_, compare_to)
        if schema is None:
            # default DB schema -> treat as public
            schema = "public"
        if schema in IGNORED_SCHEMAS:
            return False
        # Only include objects that are in `public` schema.
        return schema == "public"

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        compare_server_default=True,
        # Render item-level changes (column type, nullable, etc.)
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create a one-shot async engine and run migrations through it."""
    # Build a fresh engine here (not the module-level one) so Alembic's
    # connection lifecycle is independent of the application's pool.
    connectable = create_async_engine(
        settings.DATABASE_URL,
        # No pool needed for one-shot migration runs
        poolclass=__import__("sqlalchemy.pool", fromlist=["NullPool"]).NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode — runs the async function."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
