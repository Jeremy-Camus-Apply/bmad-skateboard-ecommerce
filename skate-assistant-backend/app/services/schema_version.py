"""Alembic schema helpers for readiness and startup drift checks."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings

logger = logging.getLogger(__name__)


def _resolve_alembic_ini() -> Path:
    return Path(__file__).resolve().parents[2] / "alembic.ini"


def get_expected_schema_version() -> str | None:
    """Return Alembic head revision declared by local migration scripts."""
    alembic_ini = _resolve_alembic_ini()
    if not alembic_ini.exists():
        logger.warning("schema_version_unavailable_missing_alembic_ini")
        return None

    config = Config(str(alembic_ini))
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


async def get_current_db_schema_version() -> str | None:
    """Read the currently applied DB revision from alembic_version."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            )
            row = result.first()
            if row is None:
                return None
            return str(row[0])
    finally:
        await engine.dispose()


async def validate_schema_compatibility() -> str | None:
    """Ensure DB revision matches local Alembic head; raise on drift."""
    expected = get_expected_schema_version()
    if expected is None:
        logger.warning("schema_version_expected_head_missing")
        return None

    current = await get_current_db_schema_version()
    if current != expected:
        raise RuntimeError(
            "Schema drift detected: "
            f"expected Alembic head '{expected}', got '{current}'. "
            "Run migrations before starting the service."
        )
    return current
