"""Pytest fixtures shared across the suite."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    # raise_app_exceptions=False lets the registered Exception handler turn
    # uncaught exceptions into 500 responses (matching production), instead of
    # propagating them up through the ASGI transport into httpx.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
