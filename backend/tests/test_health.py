"""
Application smoke tests.

These tests use HTTPX's ASGITransport to drive the FastAPI app in-process
without binding a real network socket or requiring a live database.

The DB engine is patched to a no-op so tests are hermetic — no Supabase
credentials are needed in CI.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(app) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def client():
    """
    Yield an async test client with:
    * lifespan disabled (we test startup/shutdown separately)
    * engine patched so no DB connection is attempted
    """
    # Patch engine.connect and engine.begin to avoid real DB calls in lifespan
    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    mock_conn.exec_driver_sql = AsyncMock(return_value=None)
    mock_conn.run_sync = AsyncMock(return_value=None)

    with (
        patch("app.database.session.engine.connect", return_value=mock_conn),
        patch("app.database.session.engine.begin", return_value=mock_conn),
        patch("app.database.session.engine.dispose", new_callable=AsyncMock),
    ):
        # Import app AFTER patching so lifespan sees the mocked engine
        from app.main import app

        async with _make_client(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_health_returns_200(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_response_shape(client: AsyncClient):
    data = (await client.get("/health")).json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "service" in data
    assert "environment" in data


@pytest.mark.anyio
async def test_health_response_has_request_id_header(client: AsyncClient):
    response = await client.get("/health")
    assert "x-request-id" in response.headers


@pytest.mark.anyio
async def test_health_accepts_caller_request_id(client: AsyncClient):
    """Server must echo back the caller-supplied request ID."""
    my_id = "my-trace-abc-123"
    response = await client.get("/health", headers={"x-request-id": my_id})
    assert response.headers["x-request-id"] == my_id


@pytest.mark.anyio
async def test_unknown_route_returns_404_json(client: AsyncClient):
    response = await client.get("/this-does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NOT_FOUND"
    assert "request_id" in body


@pytest.mark.anyio
async def test_cors_preflight(client: AsyncClient):
    """OPTIONS preflight should return 200 with CORS headers."""
    response = await client.options(
        "/health",
        headers={
            "origin": "http://localhost:3000",
            "access-control-request-method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
