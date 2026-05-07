"""Smoke tests for the operational endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from app.main import create_app
from httpx import ASGITransport
from httpx import AsyncClient


@pytest.fixture
async def client_no_schema_guard(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    import app.main as main_module
    from app.api.v1 import ops as ops_module

    async def _fake_schema_check() -> str:
        return "20260507_0001"

    async def _fake_current_schema_version() -> str:
        return "20260507_0001"

    monkeypatch.setattr(main_module, "validate_schema_compatibility", _fake_schema_check)
    monkeypatch.setattr(
        ops_module, "get_current_db_schema_version", _fake_current_schema_version
    )

    app = create_app()
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_returns_expected_shape(client_no_schema_guard: AsyncClient) -> None:
    response = await client_no_schema_guard.get("/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload
    assert payload["schema_version"] == "20260507_0001"


@pytest.mark.asyncio
async def test_readiness_returns_expected_shape(client_no_schema_guard: AsyncClient) -> None:
    response = await client_no_schema_guard.get("/v1/readiness")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload


@pytest.mark.asyncio
async def test_request_id_is_returned_in_header(client_no_schema_guard: AsyncClient) -> None:
    response = await client_no_schema_guard.get("/v1/health")
    assert "x-request-id" in {k.lower() for k in response.headers}


@pytest.mark.asyncio
async def test_request_id_is_propagated_when_provided(
    client_no_schema_guard: AsyncClient,
) -> None:
    incoming = "test-correlation-12345"
    response = await client_no_schema_guard.get("/v1/health", headers={"X-Request-Id": incoming})
    assert response.headers["x-request-id"] == incoming
