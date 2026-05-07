"""Story 1.5 — request/event schema validation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.api.v1 import chat as chat_api
from app.api.v1.schemas import ChatTurnRequest
from pydantic import ValidationError


def test_chat_turn_request_requires_message_for_new_turn() -> None:
    with pytest.raises(ValidationError):
        ChatTurnRequest.model_validate({"message": ""})


def test_chat_turn_request_allows_resume_without_message() -> None:
    req = ChatTurnRequest.model_validate({"turn_id": str(uuid4())})
    assert req.message == ""


def test_sse_keepalive_comment_literal_matches_story_contract() -> None:
    assert chat_api._HEARTBEAT_BYTES == b": heartbeat\n\n"
