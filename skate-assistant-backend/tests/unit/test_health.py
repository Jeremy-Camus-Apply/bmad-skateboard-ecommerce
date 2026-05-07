"""Smoke tests for the operational endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_expected_shape(client: AsyncClient) -> None:
    response = await client.get("/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload
    assert payload["schema_version"] == "20260507_0001"


@pytest.mark.asyncio
async def test_readiness_returns_expected_shape(client: AsyncClient) -> None:
    response = await client.get("/v1/readiness")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload


@pytest.mark.asyncio
async def test_request_id_is_returned_in_header(client: AsyncClient) -> None:
    response = await client.get("/v1/health")
    assert "x-request-id" in {k.lower() for k in response.headers}


@pytest.mark.asyncio
async def test_request_id_is_propagated_when_provided(client: AsyncClient) -> None:
    incoming = "test-correlation-12345"
    response = await client.get("/v1/health", headers={"X-Request-Id": incoming})
    assert response.headers["x-request-id"] == incoming
