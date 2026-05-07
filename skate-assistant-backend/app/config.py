"""Application configuration via Pydantic Settings (env-driven).

Settings are accessed lazily via `get_settings()` (cached). This avoids
import-time crashes when env vars are malformed — instead, the failure
surfaces at first call, with a clearer traceback.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    environment: Literal["local", "dev", "staging", "prod"] = "local"
    region: str = "us-central1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    git_commit_sha: str = "unknown"

    database_url: str = Field(
        default="postgresql+asyncpg://assistant:assistant@localhost:5432/assistant",
    )
    redis_url: str = "redis://localhost:6379/0"

    otel_service_name: str = "skate-assistant-backend"
    otel_traces_exporter: Literal["gcp_trace", "console", "none"] = "console"
    google_cloud_project: str = ""

    secret_firebase_admin_credentials: str = ""
    secret_anthropic_api_key: str = ""
    secret_langfuse_api_key: str = ""
    secret_anonymous_jwt_signing: str = ""

    firebase_auth_emulator_host: str = ""
    firestore_emulator_host: str = ""

    @field_validator("log_level", mode="before")
    @classmethod
    def _uppercase_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    @field_validator("database_url")
    @classmethod
    def _require_asyncpg_driver(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "database_url must use the asyncpg driver "
                "(postgresql+asyncpg://...). "
                "Sync drivers will fail at runtime against async engine code."
            )
        return value

    @model_validator(mode="after")
    def _require_gcp_project_when_cloud_trace(self) -> Settings:
        if self.otel_traces_exporter == "gcp_trace" and not self.google_cloud_project:
            raise ValueError(
                "google_cloud_project is required when otel_traces_exporter=gcp_trace. "
                "Set GOOGLE_CLOUD_PROJECT env var or change OTEL_TRACES_EXPORTER."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings instance.

    Cached so we pay validation once per process. Tests can call
    `get_settings.cache_clear()` to force re-read after mutating env.
    """
    return Settings()
