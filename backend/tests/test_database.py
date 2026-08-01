"""
tests/test_database.py
======================
Repository and session layer tests.

All tests use an **in-memory SQLite** database via ``aiosqlite`` so they:
* Run without a live PostgreSQL / Supabase instance.
* Are hermetic — each test gets a fresh schema via ``create_all()`` /
  ``drop_all()`` and a fresh session.
* Are fast — no network latency.

SQLite dialect differences handled
-----------------------------------
* SQLite does not support ``UUID`` columns natively — we override the
  ``DATABASE_URL`` with ``sqlite+aiosqlite:///:memory:`` and use
  ``CHAR(36)`` as the UUID type for the test engine.
* PostgreSQL-specific types (``JSONB``) fall back to ``JSON`` in SQLite
  automatically via SQLAlchemy's dialect mapping.
* ``postgresql.UUID`` columns require a render_as_batch workaround —
  we use ``render_as_batch=True`` in the test Alembic config if needed,
  but for these tests we bypass Alembic entirely and call ``create_all``.
"""

from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# ── Override dialect-specific types before importing models ──────────────────
# Patch UUID to use String(36) for SQLite compatibility.
import sqlalchemy.dialects.postgresql as pg_dialect
from sqlalchemy import String

_orig_uuid = pg_dialect.UUID
pg_dialect.UUID = lambda **kw: String(36)  # type: ignore[assignment]

# Now import models (they will use the patched UUID)
from app.models.base import Base
from app.models.project import Project
from app.models.scene import Scene
from app.models.agent_session import AgentSession
from app.database.repository import BaseRepository

# Restore original type so other tests are unaffected
pg_dialect.UUID = _orig_uuid  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a fresh AsyncSession backed by an in-memory SQLite database.

    Schema is created before the test and dropped after, giving full isolation.
    Uses ``StaticPool`` so the same in-memory DB is shared across the single
    connection that the test uses.
    """
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Helper: concrete repositories bound to the test session
# ---------------------------------------------------------------------------

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Project, session)


class SceneRepository(BaseRepository[Scene]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Scene, session)


class AgentSessionRepository(BaseRepository[AgentSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AgentSession, session)


# ---------------------------------------------------------------------------
# BaseRepository.create / get
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_get_project(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    project = Project(title="Noir City", genre="Thriller", status="draft")

    created = await repo.create(project)
    assert created.id is not None
    assert created.title == "Noir City"

    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.title == "Noir City"


# ---------------------------------------------------------------------------
# BaseRepository.get_or_raise
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_or_raise_raises_for_missing_record(db_session: AsyncSession):
    from app.exceptions import NotFoundError

    repo = ProjectRepository(db_session)
    missing_id = str(uuid.uuid4())

    with pytest.raises(NotFoundError):
        await repo.get_or_raise(missing_id)


# ---------------------------------------------------------------------------
# BaseRepository.list + count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_returns_all_projects(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    for i in range(3):
        await repo.create(Project(title=f"Project {i}", status="draft"))

    items = await repo.list()
    assert len(items) == 3


@pytest.mark.asyncio
async def test_count_returns_correct_total(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    for _ in range(5):
        await repo.create(Project(title="Film", status="draft"))

    total = await repo.count()
    assert total == 5


# ---------------------------------------------------------------------------
# BaseRepository.filter_by
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_filter_by_status(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    await repo.create(Project(title="A", status="draft"))
    await repo.create(Project(title="B", status="in_progress"))
    await repo.create(Project(title="C", status="draft"))

    drafts = await repo.filter_by(status="draft")
    assert len(drafts) == 2
    assert all(p.status == "draft" for p in drafts)


# ---------------------------------------------------------------------------
# BaseRepository.exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exists_true_and_false(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    await repo.create(Project(title="Ghost Film", status="completed"))

    assert await repo.exists(status="completed") is True
    assert await repo.exists(status="archived") is False


# ---------------------------------------------------------------------------
# BaseRepository.update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_modifies_fields(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    project = await repo.create(Project(title="Old Title", status="draft"))

    updated = await repo.update(project, title="New Title", status="in_progress")
    assert updated.title == "New Title"
    assert updated.status == "in_progress"


# ---------------------------------------------------------------------------
# BaseRepository.bulk_create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_create_inserts_all(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    projects = [Project(title=f"Batch {i}", status="draft") for i in range(4)]

    created = await repo.bulk_create(projects)
    assert len(created) == 4
    assert await repo.count() == 4


# ---------------------------------------------------------------------------
# BaseRepository.delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_removes_record(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    project = await repo.create(Project(title="Delete Me", status="draft"))

    await repo.delete(project)
    assert await repo.get(project.id) is None
    assert await repo.count() == 0


# ---------------------------------------------------------------------------
# BaseRepository.paginate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paginate_returns_correct_pages(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    for i in range(7):
        await repo.create(Project(title=f"Film {i}", status="draft"))

    page1, total = await repo.paginate(page=1, page_size=3)
    page2, _ = await repo.paginate(page=2, page_size=3)
    page3, _ = await repo.paginate(page=3, page_size=3)

    assert total == 7
    assert len(page1) == 3
    assert len(page2) == 3
    assert len(page3) == 1  # remainder


# ---------------------------------------------------------------------------
# Scene — FK relationship + unique constraint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scene_belongs_to_project(db_session: AsyncSession):
    project_repo = ProjectRepository(db_session)
    scene_repo = SceneRepository(db_session)

    project = await project_repo.create(Project(title="Sci-Fi Epic", status="draft"))
    scene = await scene_repo.create(
        Scene(
            project_id=project.id,
            scene_number=1,
            title="Opening Shot",
            int_ext="EXT",
            time_of_day="DAY",
        )
    )

    assert scene.project_id == project.id
    assert scene.title == "Opening Shot"


# ---------------------------------------------------------------------------
# Model.to_dict()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_to_dict_returns_all_columns(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    project = await repo.create(Project(title="Dict Test", status="draft"))

    d = project.to_dict()
    assert "id" in d
    assert "title" in d
    assert d["title"] == "Dict Test"
    assert "created_at" in d
    assert "updated_at" in d


# ---------------------------------------------------------------------------
# Model.__repr__()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repr_includes_class_name_and_pk(db_session: AsyncSession):
    repo = ProjectRepository(db_session)
    project = await repo.create(Project(title="Repr Test", status="draft"))

    r = repr(project)
    assert "Project" in r
    assert str(project.id) in r
