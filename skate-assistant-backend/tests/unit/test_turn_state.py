"""Story 1.5 — turn buffer + resume primitives."""

from __future__ import annotations

import asyncio

import pytest
from app.services.turn_state import BufferedSseEvent, TurnBuffer, TurnSession


@pytest.mark.asyncio
async def test_turn_buffer_monotonic_wait_next_after() -> None:
    buf = TurnBuffer()

    async def producer() -> None:
        await asyncio.sleep(0.01)
        await buf.append(BufferedSseEvent(1, "token", {"turn_id": "t", "event_id": 1}))
        await buf.append(BufferedSseEvent(2, "done", {"turn_id": "t", "event_id": 2}))

    task = asyncio.create_task(producer())

    first = await buf.wait_next_after(0)
    assert first is not None
    assert first.event_id == 1

    second = await buf.wait_next_after(1)
    assert second is not None
    assert second.event_id == 2

    third = await buf.wait_next_after(2)
    assert third is None

    await task


def test_turn_session_expires_based_on_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    buf = TurnBuffer()
    session = TurnSession(turn_id="t1", buffer=buf, ttl_seconds=300.0)

    monkeypatch.setattr("app.services.turn_state.time.monotonic", lambda: 0.0)
    session.touch()

    monkeypatch.setattr("app.services.turn_state.time.monotonic", lambda: 400.0)
    assert session.is_expired() is True
