"""Pydantic schemas for `/v1/chat/*` (Story 1.5)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ChatTurnRequest(BaseModel):
    """Body for `POST /v1/chat/turn`.

    - **New turn:** omit `turn_id`, provide non-empty `message`.
    - **Resume / replay:** set `turn_id` to an existing turn (optional `message`, ignored).
    """

    message: str = Field(default="", max_length=8000)
    turn_id: UUID | None = None

    @model_validator(mode="after")
    def _validate_new_vs_resume(self) -> ChatTurnRequest:
        if self.turn_id is None and not self.message.strip():
            raise ValueError("message is required when starting a new turn")
        return self


class ErrorEventPayload(BaseModel):
    """Structured error envelope embedded in SSE `error` events."""

    turn_id: str
    event_id: int
    code: str
    message: str
    request_id: str
    retry_after: int | None = None
    details: dict[str, Any] | list[Any] | None = None
