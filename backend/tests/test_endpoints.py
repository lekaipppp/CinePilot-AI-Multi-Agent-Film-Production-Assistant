"""
tests/test_endpoints.py
=======================
Integration-style tests for all 5 domain endpoint groups.

Strategy
--------
* Uses ``httpx.AsyncClient`` with ``ASGITransport`` — no real network, no real DB.
* Every service dependency that touches the database is overridden via
  ``app.dependency_overrides`` with a lightweight ``AsyncMock`` / plain mock.
* Tests verify routing, HTTP status codes, response shape, and that the
  correct service methods are called with the correct arguments.
* No Gemini / LangGraph code is executed — ``workflow_runner.run`` is patched.

Running
-------
    pytest tests/test_endpoints.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app

# ─────────────────────────── helpers ───────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _project_row(
    project_id: uuid.UUID | None = None,
    title: str = "Test Film",
    status: str = "draft",
) -> MagicMock:
    """Return a MagicMock that quacks like a Project ORM row."""
    row = MagicMock()
    row.id           = project_id or uuid.uuid4()
    row.title        = title
    row.genre        = "Thriller"
    row.logline      = "A test logline."
    row.status       = status
    row.script_draft = None
    row.created_at   = _now()
    row.updated_at   = _now()
    return row


# ─────────────────────────── fixtures ──────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    """Create a fresh FastAPI application instance for the test module."""
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP test client with ASGI transport."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ─────────────────────────── /projects ─────────────────────────────────────────

class TestProjectsRouter:
    """Tests for GET /api/v1/projects/ and GET /api/v1/projects/{id}."""

    @pytest.mark.asyncio
    async def test_list_projects_returns_200(self, client, app):
        """GET /projects/ should return a list (may be empty)."""
        mock_svc = MagicMock()
        mock_svc.list = AsyncMock(return_value=[])

        from app.deps import get_project_service
        app.dependency_overrides[get_project_service] = lambda: mock_svc

        resp = await client.get("/api/v1/projects/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        mock_svc.list.assert_called_once_with(limit=20, offset=0)

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_project_returns_201(self, client, app):
        """POST /projects/ should return 201 with the created project."""
        project = _project_row()
        mock_svc = MagicMock()
        mock_svc.create = AsyncMock(return_value=project)

        from app.deps import get_project_service
        app.dependency_overrides[get_project_service] = lambda: mock_svc

        resp = await client.post(
            "/api/v1/projects/",
            json={"title": "Test Film", "genre": "Thriller"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Film"
        assert "id" in data

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_project_detail_returns_200(self, client, app):
        """GET /projects/{id} should return ProjectDetailRead with derived fields."""
        project_id = uuid.uuid4()
        detail = MagicMock()
        detail.id                    = project_id
        detail.title                 = "Test Film"
        detail.genre                 = "Drama"
        detail.logline               = None
        detail.status                = "draft"
        detail.created_at            = _now()
        detail.updated_at            = _now()
        detail.has_script            = False
        detail.script_preview        = None
        detail.scene_count           = 0
        detail.has_schedule          = False
        detail.has_budget            = False
        detail.risk_report_count     = 0
        detail.latest_session_status = None

        # Return a Pydantic-serialisable dict from model_dump
        from app.schemas.project import ProjectDetailRead
        detail_schema = ProjectDetailRead(
            id=project_id,
            title="Test Film",
            genre="Drama",
            logline=None,
            status="draft",
            created_at=_now(),
            updated_at=_now(),
            has_script=False,
            script_preview=None,
            scene_count=0,
            has_schedule=False,
            has_budget=False,
            risk_report_count=0,
            latest_session_status=None,
        )

        mock_svc = MagicMock()
        mock_svc.get_detail = AsyncMock(return_value=detail_schema)

        from app.deps import get_project_service
        app.dependency_overrides[get_project_service] = lambda: mock_svc

        resp = await client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(project_id)
        assert "has_script" in data
        assert "scene_count" in data
        assert "latest_session_status" in data

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client, app):
        """GET /projects/{id} should return 404 for unknown project."""
        from fastapi import HTTPException, status as http_status
        mock_svc = MagicMock()
        mock_svc.get_detail = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Project not found.")
        )

        from app.deps import get_project_service
        app.dependency_overrides[get_project_service] = lambda: mock_svc

        resp = await client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert resp.status_code == 404

        app.dependency_overrides.clear()


# ─────────────────────────── /script ───────────────────────────────────────────

class TestScriptRouter:
    """Tests for POST /script/upload-script."""

    @pytest.mark.asyncio
    async def test_upload_script_returns_200(self, client, app):
        """POST /script/upload-script should persist the screenplay and return 200."""
        project_id = uuid.uuid4()
        screenplay = "FADE IN:\n\nEXT. CITY STREET - DAY\n\nA bustling metropolis." + " x" * 30

        project = _project_row(project_id=project_id)
        project.script_draft = screenplay

        mock_svc = MagicMock()
        mock_svc.upload = AsyncMock(return_value=project)

        from app.deps import get_script_service
        app.dependency_overrides[get_script_service] = lambda: mock_svc

        resp = await client.post(
            "/api/v1/script/upload-script",
            json={"project_id": str(project_id), "screenplay": screenplay},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == str(project_id)
        assert data["character_count"] == len(screenplay)
        assert "screenplay_preview" in data
        mock_svc.upload.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_script_short_screenplay_rejected(self, client, app):
        """Screenplay under 50 chars should be rejected with 422 by Pydantic."""
        project_id = uuid.uuid4()

        # No service mock needed — Pydantic rejects before the handler runs
        resp = await client.post(
            "/api/v1/script/upload-script",
            json={"project_id": str(project_id), "screenplay": "too short"},
        )
        assert resp.status_code == 422


# ─────────────────────────── /pipeline ─────────────────────────────────────────

class TestPipelineRouter:
    """Tests for POST /pipeline/run and GET /pipeline/status/{id}."""

    @pytest.mark.asyncio
    async def test_run_pipeline_returns_200(self, client, app):
        """POST /pipeline/run should trigger the pipeline and return the plan."""
        project_id = uuid.uuid4()
        session_id = uuid.uuid4()

        mock_session = MagicMock()
        mock_session.id            = session_id
        mock_session.project_id    = project_id
        mock_session.agent_type    = "production_planning"
        mock_session.status        = "completed"
        mock_session.error_message = None
        mock_session.completed_at  = _now()
        mock_session.created_at    = _now()
        mock_session.updated_at    = _now()
        mock_session.state_snapshot = {
            "status": "complete",
            "run_metadata": {
                "run_id": str(uuid.uuid4()),
                "project_id": str(project_id),
                "started_at": "2025-01-01T00:00:00Z",
                "graph_version": "1.0",
                "elapsed_secs": 12.5,
            },
        }

        mock_svc = MagicMock()
        mock_svc.run = AsyncMock(return_value=mock_session)

        from app.deps import get_pipeline_service
        app.dependency_overrides[get_pipeline_service] = lambda: mock_svc

        resp = await client.post(
            "/api/v1/pipeline/run",
            json={"project_id": str(project_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == str(session_id)
        assert data["status"] == "complete"
        assert "production_plan" in data
        mock_svc.run.assert_called_once_with(
            project_id=project_id,
            input_overrides=None,
        )

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_run_pipeline_no_script_returns_422(self, client, app):
        """POST /pipeline/run should propagate 422 when no screenplay is set."""
        from fastapi import HTTPException
        mock_svc = MagicMock()
        mock_svc.run = AsyncMock(
            side_effect=HTTPException(
                status_code=422,
                detail="Project has no screenplay.",
            )
        )

        from app.deps import get_pipeline_service
        app.dependency_overrides[get_pipeline_service] = lambda: mock_svc

        resp = await client.post(
            "/api/v1/pipeline/run",
            json={"project_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 422

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_pipeline_status_returns_200(self, client, app):
        """GET /pipeline/status/{id} should return the session status."""
        session_id = uuid.uuid4()
        project_id = uuid.uuid4()

        mock_session = MagicMock()
        mock_session.id            = session_id
        mock_session.project_id    = project_id
        mock_session.agent_type    = "production_planning"
        mock_session.status        = "completed"
        mock_session.error_message = None
        mock_session.completed_at  = _now()
        mock_session.created_at    = _now()
        mock_session.updated_at    = _now()

        mock_svc = MagicMock()
        mock_svc.get_or_404 = AsyncMock(return_value=mock_session)

        from app.deps import get_agent_session_service
        app.dependency_overrides[get_agent_session_service] = lambda: mock_svc

        resp = await client.get(f"/api/v1/pipeline/status/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == str(session_id)
        assert data["status"] == "completed"

        app.dependency_overrides.clear()


# ─────────────────────────── /budget ───────────────────────────────────────────

class TestBudgetRouter:
    """Tests for GET /budget/{project_id} and POST /budget/update."""

    def _make_budget_mock(
        self,
        project_id: uuid.UUID,
        budget_id: uuid.UUID | None = None,
    ) -> MagicMock:
        b = MagicMock()
        b.id                   = budget_id or uuid.uuid4()
        b.project_id           = project_id
        b.currency             = "USD"
        b.total_estimated_cost = 150000.00
        b.contingency_pct      = 15.0
        b.status               = "draft"
        b.assumptions          = "Indie production assumptions."
        b.items                = []
        b.created_at           = _now()
        b.updated_at           = _now()
        return b

    @pytest.mark.asyncio
    async def test_get_budget_returns_200(self, client, app):
        """GET /budget/{project_id} should return the budget with items."""
        project_id = uuid.uuid4()
        mock_budget = self._make_budget_mock(project_id)

        mock_svc = MagicMock()
        mock_svc.get_by_project = AsyncMock(return_value=mock_budget)

        from app.deps import get_budget_service
        app.dependency_overrides[get_budget_service] = lambda: mock_svc

        resp = await client.get(f"/api/v1/budget/{project_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["currency"] == "USD"
        assert "items" in data

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_budget_returns_200(self, client, app):
        """POST /budget/update should upsert the budget and return BudgetRead."""
        project_id = uuid.uuid4()
        mock_budget = self._make_budget_mock(project_id)

        mock_svc = MagicMock()
        mock_svc.upsert = AsyncMock(return_value=mock_budget)

        from app.deps import get_budget_service
        app.dependency_overrides[get_budget_service] = lambda: mock_svc

        resp = await client.post(
            "/api/v1/budget/update",
            json={
                "project_id": str(project_id),
                "currency": "USD",
                "contingency_pct": 15.0,
                "items": [
                    {
                        "category": "cast",
                        "label": "Lead Actor Fee",
                        "amount": 50000.00,
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["currency"] == "USD"
        mock_svc.upsert.assert_called_once()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_budget_not_found(self, client, app):
        """GET /budget/{project_id} should return 404 when no budget exists."""
        from fastapi import HTTPException
        mock_svc = MagicMock()
        mock_svc.get_by_project = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="No budget found.")
        )

        from app.deps import get_budget_service
        app.dependency_overrides[get_budget_service] = lambda: mock_svc

        resp = await client.get(f"/api/v1/budget/{uuid.uuid4()}")
        assert resp.status_code == 404

        app.dependency_overrides.clear()


# ─────────────────────────── /schedule ─────────────────────────────────────────

class TestScheduleRouter:
    """Tests for GET /schedule/{project_id}."""

    @pytest.mark.asyncio
    async def test_get_schedule_returns_200(self, client, app):
        """GET /schedule/{project_id} should return ScheduleRead with days."""
        project_id = uuid.uuid4()

        mock_schedule = MagicMock()
        mock_schedule.id               = uuid.uuid4()
        mock_schedule.project_id       = project_id
        mock_schedule.total_shoot_days = 5
        mock_schedule.status           = "draft"
        mock_schedule.notes            = "Shooting in Vancouver."
        mock_schedule.days             = []
        mock_schedule.created_at       = _now()
        mock_schedule.updated_at       = _now()

        mock_svc = MagicMock()
        mock_svc.get_by_project = AsyncMock(return_value=mock_schedule)

        from app.deps import get_schedule_service
        app.dependency_overrides[get_schedule_service] = lambda: mock_svc

        resp = await client.get(f"/api/v1/schedule/{project_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_shoot_days"] == 5
        assert isinstance(data["days"], list)

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, client, app):
        """GET /schedule/{project_id} should return 404 when no schedule exists."""
        from fastapi import HTTPException
        mock_svc = MagicMock()
        mock_svc.get_by_project = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="No schedule found.")
        )

        from app.deps import get_schedule_service
        app.dependency_overrides[get_schedule_service] = lambda: mock_svc

        resp = await client.get(f"/api/v1/schedule/{uuid.uuid4()}")
        assert resp.status_code == 404

        app.dependency_overrides.clear()
