"""Pytest fixtures shared across the suite."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from app.config import get_settings
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def _story_15_test_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "SECRET_ANONYMOUS_JWT_SIGNING",
        "unit-test-anonymous-jwt-secret-key-at-least-32-bytes-long-xx",
    )
    monkeypatch.setenv("SECRET_FIREBASE_ADMIN_CREDENTIALS", "")
    monkeypatch.setenv("CHAT_TURN_HEARTBEAT_SECONDS", "0.05")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    # raise_app_exceptions=False lets the registered Exception handler turn
    # uncaught exceptions into 500 responses (matching production), instead of
    # propagating them up through the ASGI transport into httpx.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
