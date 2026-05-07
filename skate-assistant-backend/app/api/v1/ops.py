"""Operational endpoints: liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(tags=["ops"])


class HealthResponse(BaseModel):
    status: str
    version: str
    schema_version: str | None


def _alembic_revision() -> str | None:
    """Return current Alembic head revision, or None if no schema yet.

    Story 1.1 leaves migrations/versions empty by design (Story 1.2 fills it).
    Returning None now keeps the JSON shape stable for downstream stories.
    """
    return None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.git_commit_sha,
        schema_version=_alembic_revision(),
    )


@router.get("/readiness", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.git_commit_sha,
        schema_version=_alembic_revision(),
    )
