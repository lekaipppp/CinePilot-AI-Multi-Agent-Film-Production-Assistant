"""
app/models/base.py
==================
Shared SQLAlchemy declarative base and reusable ORM mixins.

All ORM model files MUST import ``Base`` from this module.

Mixins
------
``UUIDPrimaryKeyMixin``
    Provides a ``id`` column of type UUID, auto-generated on the Python side
    with ``uuid.uuid4()``.  Using Python-side generation means the primary key
    is available *before* the INSERT reaches the database (avoids an extra
    SELECT after flush) and prevents conflicts in bulk operations.

``TimestampMixin``
    Provides ``created_at`` and ``updated_at`` columns, both timezone-aware.
    ``created_at`` uses a PostgreSQL server-side default (``NOW()``) so it is
    accurate even when rows are inserted via raw SQL or migrations.
    ``updated_at`` uses SQLAlchemy's ``onupdate`` hook for ORM-driven updates,
    *and* also a server default so it is set on INSERT.

Design decisions
----------------
* ``expire_on_commit=False`` is set on the session factory, so accessing
  attributes after commit does not trigger implicit lazy loads.
* ``__repr__`` on the base gives every model a consistent debug representation.
* ``to_dict()`` is a convenience method for logging / tests — it is *not*
  intended to replace Pydantic schemas as the serialisation layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """
    Project-wide SQLAlchemy declarative base.

    All model classes must inherit from this (directly or via a mixin chain).
    Keeping a single Base ensures a single shared ``MetaData`` object, which
    is required for Alembic autogenerate and ``create_all()`` to work.
    """

    def __repr__(self) -> str:
        """
        Generic repr that shows the model class name and its primary-key value.
        Makes debugging interactive sessions and test failures much easier.
        """
        pk_cols = self.__mapper__.primary_key
        pk_vals = {col.name: getattr(self, col.name, "?") for col in pk_cols}
        pk_str = ", ".join(f"{k}={v!r}" for k, v in pk_vals.items())
        return f"<{self.__class__.__name__} {pk_str}>"

    def to_dict(self) -> dict[str, Any]:
        """
        Return a plain dictionary of all mapped column values.

        Intended for logging and test assertions only.
        Use Pydantic schemas (``app/schemas/``) for API serialisation.
        """
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class UUIDPrimaryKeyMixin:
    """
    Adds a ``id`` UUID primary-key column with Python-side generation.

    Python-side default (``default=uuid.uuid4``) is preferred over
    ``server_default=gen_random_uuid()`` because:
    * The ID is available immediately after ``session.add(obj)`` without
      needing a round-trip ``RETURNING`` clause.
    * Works identically in tests with SQLite (which has no ``gen_random_uuid``).
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        # Index is implicit on primary key; set index=False to suppress the
        # redundant index Alembic would otherwise emit.
        index=False,
    )


class TimestampMixin:
    """
    Adds ``created_at`` and ``updated_at`` timestamp columns.

    Both are timezone-aware (``TIMESTAMPTZ`` in PostgreSQL).

    ``created_at``  — set once on INSERT, never changed.
    ``updated_at``  — set on INSERT; refreshed on every ORM UPDATE via
                      ``onupdate=func.now()``.

    Note: ``onupdate`` fires on ORM-driven UPDATEs only.  Raw SQL UPDATEs
    bypass it.  For that case, add a PostgreSQL trigger or use Supabase's
    ``moddatetime`` extension.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
