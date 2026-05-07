"""Story 1.5 — `/v1/chat/turn` SSE integration coverage."""

from __future__ import annotations

import pytest
from app.api.v1 import chat as chat_api
from app.models.errors import ChatErrorCode
from app.services.turn_state import TurnSession
from fastapi import Request
from httpx import AsyncClient

from tests.helpers import (
    json_data,
    mint_anonymous_session_jwt,
    parse_sse_blocks,
    sse_events,
)


def _anon_secret() -> str:
    return "unit-test-anonymous-jwt-secret-key-at-least-32-bytes-long-xx"


@pytest.mark.asyncio
async def test_chat_turn_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/v1/chat/turn", json={"message": "hello"})
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "HTTP_401"


@pytest.mark.asyncio
async def test_chat_turn_rejects_invalid_anonymous_jwt(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/chat/turn",
        json={"message": "hello"},
        headers={"X-Anonymous-Session": "not-a-jwt"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_turn_streams_placeholder_sequence(client: AsyncClient) -> None:
    token = mint_anonymous_session_jwt(secret=_anon_secret())
    resp = await client.post(
        "/v1/chat/turn",
        json={"message": "Need a street deck"},
        headers={"X-Anonymous-Session": token},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    blocks = parse_sse_blocks(resp.text)
    events = sse_events(blocks)
    assert [e["event"] for e in events] == ["token", "recommendation", "done"]

    ids = [int(e["id"]) for e in events]
    assert ids == [1, 2, 3]

    token_payload = json_data(events[0])
    turn_id = str(token_payload["turn_id"])
    assert token_payload["event_id"] == 1

    done_payload = json_data(events[-1])
    assert done_payload["turn_id"] == turn_id
    assert done_payload["event_id"] == 3


@pytest.mark.asyncio
async def test_chat_turn_resume_replays_after_last_event_id(client: AsyncClient) -> None:
    token = mint_anonymous_session_jwt(secret=_anon_secret())

    first = await client.post(
        "/v1/chat/turn",
        json={"message": "hello"},
        headers={"X-Anonymous-Session": token},
    )
    assert first.status_code == 200
    events = sse_events(parse_sse_blocks(first.text))
    turn_id = str(json_data(events[0])["turn_id"])

    second = await client.post(
        "/v1/chat/turn",
        json={"message": "", "turn_id": turn_id},
        headers={"X-Anonymous-Session": token, "Last-Event-ID": "1"},
    )
    assert second.status_code == 200
    resumed = sse_events(parse_sse_blocks(second.text))
    assert [e["event"] for e in resumed] == ["recommendation", "done"]
    assert [int(e["id"]) for e in resumed] == [2, 3]


@pytest.mark.asyncio
async def test_chat_turn_expired_resume_returns_error_terminal(client: AsyncClient) -> None:
    token = mint_anonymous_session_jwt(secret=_anon_secret())

    first = await client.post(
        "/v1/chat/turn",
        json={"message": "hello"},
        headers={"X-Anonymous-Session": token},
    )
    assert first.status_code == 200
    events = sse_events(parse_sse_blocks(first.text))
    turn_id = str(json_data(events[0])["turn_id"])

    from app.services.turn_state import GLOBAL_TURN_SESSION_STORE

    session = await GLOBAL_TURN_SESSION_STORE.get_session(turn_id)
    assert session is not None
    session.last_activity_monotonic = 0.0

    second = await client.post(
        "/v1/chat/turn",
        json={"message": "", "turn_id": turn_id},
        headers={"X-Anonymous-Session": token},
    )
    assert second.status_code == 200
    resumed = sse_events(parse_sse_blocks(second.text))
    assert len(resumed) == 1
    assert resumed[0]["event"] == "error"
    payload = json_data(resumed[0])
    assert payload["code"] == "TURN_EXPIRED"


@pytest.mark.asyncio
async def test_chat_turn_failure_emits_single_error_terminal(
    monkeypatch: pytest.MonkeyPatch, client: AsyncClient
) -> None:
    token = mint_anonymous_session_jwt(secret=_anon_secret())

    async def boom(*, session: TurnSession, request: Request, message: str) -> None:
        _ = message
        request_id = getattr(request.state, "request_id", "")
        await chat_api._append_sse_event(session, "token", {"text": "hi"})
        await chat_api._append_terminal_error_event(
            session=session,
            request_id=request_id,
            code=ChatErrorCode.INTERNAL_ERROR,
            message="Internal server error",
            details={"error": "forced failure"},
        )

    monkeypatch.setattr(chat_api, "run_placeholder_turn", boom)

    resp = await client.post(
        "/v1/chat/turn",
        json={"message": "hello"},
        headers={"X-Anonymous-Session": token},
    )
    assert resp.status_code == 200
    events = sse_events(parse_sse_blocks(resp.text))
    assert [e["event"] for e in events] == ["token", "error"]
    payload = json_data(events[-1])
    assert payload["code"] == "INTERNAL_ERROR"
