"""Machine-readable chat / gateway error codes (architecture + Story 1.5)."""

from __future__ import annotations

from enum import StrEnum


class ChatErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTH_FAILED = "AUTH_FAILED"
    TURN_EXPIRED = "TURN_EXPIRED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
