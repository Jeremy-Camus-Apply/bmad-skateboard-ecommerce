"""Smoke tests for the structured-error-envelope handlers."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from httpx import AsyncClient


@pytest.fixture
async def client_with_error_routes(client: AsyncClient) -> AsyncClient:
    """Add a couple of error-producing routes onto the same app for smoke coverage.

    We mutate the underlying app via the transport so we don't need a separate
    factory. The routes are scoped to this test only.
    """
    app = client._transport.app  # type: ignore[attr-defined]

    @app.get("/_test/raise-http")
    async def _raise_http() -> None:
        raise HTTPException(status_code=418, detail="I am a teapot")

    @app.get("/_test/raise-unhandled")
    async def _raise_unhandled() -> None:
        raise RuntimeError("boom")

    return client


@pytest.mark.asyncio
async def test_http_exception_envelope_shape(
    client_with_error_routes: AsyncClient,
) -> None:
    response = await client_with_error_routes.get("/_test/raise-http")
    assert response.status_code == 418

    payload = response.json()
    assert payload["code"] == "HTTP_418"
    assert payload["message"] == "I am a teapot"
    assert "request_id" in payload and isinstance(payload["request_id"], str)
    assert response.headers.get("x-request-id") == payload["request_id"]


@pytest.mark.asyncio
async def test_unhandled_exception_envelope_shape(
    client_with_error_routes: AsyncClient,
) -> None:
    response = await client_with_error_routes.get("/_test/raise-unhandled")
    assert response.status_code == 500

    payload = response.json()
    assert payload["code"] == "INTERNAL_ERROR"
    assert payload["message"] == "Internal server error"
    assert "request_id" in payload and isinstance(payload["request_id"], str)
    # X-Request-Id is preserved on error responses (M1 fix).
    assert response.headers.get("x-request-id") == payload["request_id"]
