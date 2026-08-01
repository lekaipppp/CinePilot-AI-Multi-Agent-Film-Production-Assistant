"""
app/database/repository.py
==========================
Generic async repository base class.

``BaseRepository[ModelType]`` provides a complete, type-safe CRUD interface
over any SQLAlchemy ORM model so concrete repository classes never duplicate
``select`` / ``add`` / ``delete`` boilerplate.

Usage
-----
Define a concrete repository by subclassing and binding the model type::

    class ProjectRepository(BaseRepository[Project]):
        def __init__(self, session: AsyncSession) -> None:
            super().__init__(Project, session)

        # Add domain-specific query methods here
        async def find_by_status(self, status: str) -> list[Project]:
            return await self.filter_by(status=status)

Provided methods
----------------
``get(id)``               – fetch by primary key (None if not found)
``get_or_raise(id)``      – fetch by primary key, raise NotFoundError if missing
``list(limit, offset)``   – paginated SELECT *
``filter_by(**kwargs)``   – WHERE col = val AND … (equality only)
``count(**kwargs)``        – COUNT(*) with optional equality filters
``exists(**kwargs)``       – EXISTS shortcut (cheaper than count)
``create(obj)``            – INSERT + flush + refresh
``update(obj, **values)``  – setattr loop + flush + refresh
``bulk_create(objs)``      – batch INSERT + flush (no individual refresh)
``delete(obj)``            – DELETE + flush
``paginate(page, size)``   – 1-based page helper that delegates to list()
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.exceptions import NotFoundError

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Type-safe async CRUD repository for a single SQLAlchemy model.

    All write operations use ``session.flush()`` instead of ``session.commit()``.
    Committing is the responsibility of the caller (the service layer or the
    ``get_db()`` dependency), which owns the transaction boundary.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, record_id: Any) -> Optional[ModelType]:
        """
        Fetch a single record by primary key.

        Returns ``None`` if the record does not exist.
        Uses ``session.get()`` which checks the identity map before hitting
        the database — effectively free for already-loaded objects.
        """
        return await self.session.get(self.model, record_id)

    async def get_or_raise(self, record_id: Any) -> ModelType:
        """
        Fetch by primary key, raise ``NotFoundError`` (HTTP 404) if absent.

        Use this in service methods where a missing record is an error
        condition that should propagate to the client.
        """
        obj = await self.session.get(self.model, record_id)
        if obj is None:
            raise NotFoundError(
                resource=self.model.__name__,
                resource_id=str(record_id),
            )
        return obj

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by=None,
    ) -> List[ModelType]:
        """
        Return a paginated list of all rows in the table.

        Parameters
        ----------
        limit:
            Maximum number of rows to return.  Capped at 200 to prevent
            accidental full-table scans via the API.
        offset:
            Number of rows to skip (0-based).
        order_by:
            SQLAlchemy column expression(s) to pass to ``.order_by()``.
            Defaults to ``None`` (database-defined order, usually insertion order).
        """
        stmt = select(self.model).offset(offset).limit(min(limit, 200))
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def filter_by(self, **kwargs: Any) -> List[ModelType]:
        """
        Return all rows where column values match the given keyword arguments.

        Only equality comparisons are supported.  For complex filters
        (range, IN, LIKE) write an explicit ``select()`` statement in
        the concrete repository subclass.

        Example::

            sessions = await repo.filter_by(project_id=pid, status="running")
        """
        stmt = select(self.model)
        for col_name, value in kwargs.items():
            col = getattr(self.model, col_name)
            stmt = stmt.where(col == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **kwargs: Any) -> int:
        """
        Return the number of rows matching the given equality filters.

        More efficient than ``len(await filter_by(...))`` because it
        issues ``COUNT(*)`` instead of fetching all rows.
        """
        stmt = select(func.count()).select_from(self.model)
        for col_name, value in kwargs.items():
            col = getattr(self.model, col_name)
            stmt = stmt.where(col == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, **kwargs: Any) -> bool:
        """
        Return True if at least one row matches the given equality filters.

        Uses ``LIMIT 1`` — cheaper than ``COUNT(*)`` when you only need
        a boolean answer.
        """
        stmt = select(self.model).limit(1)
        for col_name, value in kwargs.items():
            col = getattr(self.model, col_name)
            stmt = stmt.where(col == value)
        result = await self.session.execute(stmt)
        return result.first() is not None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def create(self, obj: ModelType) -> ModelType:
        """
        Persist a new record to the database.

        Flushes the session so the database assigns server-side defaults
        (e.g. ``created_at``), then refreshes the object so those values
        are available on the returned instance without an extra query.
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType, **values: Any) -> ModelType:
        """
        Update specific fields on an already-loaded ORM object.

        Only the provided ``values`` are changed; all other attributes
        remain intact.  Flushes and refreshes after the update.

        Example::

            project = await repo.update(project, status="in_progress")
        """
        for field, value in values.items():
            setattr(obj, field, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def bulk_create(self, objs: List[ModelType]) -> List[ModelType]:
        """
        Insert a list of ORM objects in a single flush.

        More efficient than calling ``create()`` in a loop because it
        batches all ``session.add()`` calls before the single ``flush()``.

        Note: individual ``refresh()`` calls are not made after bulk insert
        to avoid N queries.  If you need server-default values (e.g.
        ``created_at``) on the returned objects, call
        ``await session.refresh(obj)`` on each item yourself.
        """
        for obj in objs:
            self.session.add(obj)
        await self.session.flush()
        return objs

    async def delete(self, obj: ModelType) -> None:
        """
        Delete a record and flush.

        Note: if the model has ``cascade="all, delete-orphan"`` relationships,
        child records are also deleted in the same flush.
        """
        await self.session.delete(obj)
        await self.session.flush()

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    async def paginate(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        order_by=None,
    ) -> tuple[List[ModelType], int]:
        """
        Return a (items, total) tuple for cursor-free page-based pagination.

        Parameters
        ----------
        page:
            1-based page number.
        page_size:
            Rows per page (capped at 200).
        order_by:
            Column expression forwarded to ``list()``.

        Returns
        -------
        items:
            Records for the requested page.
        total:
            Total row count (before pagination) — needed to compute
            ``has_next_page`` on the client.
        """
        page = max(1, page)
        size = min(page_size, 200)
        offset = (page - 1) * size

        items = await self.list(limit=size, offset=offset, order_by=order_by)
        total = await self.count()
        return items, total
