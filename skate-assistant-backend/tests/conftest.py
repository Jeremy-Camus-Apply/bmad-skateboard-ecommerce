"""Pytest fixtures shared across the suite."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # Most unit tests don't exercise live DB startup checks. Patch schema guard
    # so app startup remains deterministic in tests that only target API shape.
    import app.main as main_module

    async def _fake_schema_check() -> str:
        return "20260507_0001"

    original_check = main_module.validate_schema_compatibility
    main_module.validate_schema_compatibility = _fake_schema_check

    app = create_app()
    # raise_app_exceptions=False lets the registered Exception handler turn
    # uncaught exceptions into 500 responses (matching production), instead of
    # propagating them up through the ASGI transport into httpx.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    finally:
        main_module.validate_schema_compatibility = original_check
