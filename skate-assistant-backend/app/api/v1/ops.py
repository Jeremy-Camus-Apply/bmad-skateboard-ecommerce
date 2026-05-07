"""Operational endpoints: liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.services.schema_version import get_current_db_schema_version

router = APIRouter(tags=["ops"])


class HealthResponse(BaseModel):
    status: str
    version: str
    schema_version: str | None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    applied_revision = await get_current_db_schema_version()
    return HealthResponse(
        status="ok",
        version=settings.git_commit_sha,
        schema_version=applied_revision,
    )


@router.get("/readiness", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    settings = get_settings()
    applied_revision = await get_current_db_schema_version()
    return HealthResponse(
        status="ok",
        version=settings.git_commit_sha,
        schema_version=applied_revision,
    )
