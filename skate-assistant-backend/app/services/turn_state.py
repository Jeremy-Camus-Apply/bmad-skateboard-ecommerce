"""In-memory turn buffering + TTL for SSE replay/resume (Story 1.5).

Cloud Run scales horizontally; this store is **per-instance best-effort** — sufficient
for the scaffolding story and local/dev. Later stories can swap for Redis/Firestore.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class BufferedSseEvent:
    event_id: int
    event_name: str
    data: dict[str, Any]


@dataclass(slots=True)
class TurnBuffer:
    """Append-only buffer with blocking readers."""

    _events: list[BufferedSseEvent] = field(default_factory=list)
    _cv: asyncio.Condition = field(default_factory=asyncio.Condition)
    _terminal: Literal["done", "error"] | None = None

    @property
    def terminal_kind(self) -> Literal["done", "error"] | None:
        return self._terminal

    async def append(self, event: BufferedSseEvent) -> None:
        async with self._cv:
            self._events.append(event)
            if event.event_name == "done":
                self._terminal = "done"
            elif event.event_name == "error":
                self._terminal = "error"
            self._cv.notify_all()

    def snapshot_after(self, last_event_id: int) -> list[BufferedSseEvent]:
        return [e for e in self._events if e.event_id > last_event_id]

    async def wait_next_after(self, last_event_id: int) -> BufferedSseEvent | None:
        """Wait until an event exists with id > last_event_id or the buffer is terminal-closed."""

        async with self._cv:
            while True:
                pending = next((e for e in self._events if e.event_id > last_event_id), None)
                if pending is not None:
                    return pending
                if self._terminal is not None:
                    return None
                await self._cv.wait()


@dataclass(slots=True)
class TurnSession:
    turn_id: str
    buffer: TurnBuffer
    ttl_seconds: float
    created_monotonic: float = field(default_factory=time.monotonic)
    last_activity_monotonic: float = field(default_factory=time.monotonic)
    task: asyncio.Task[None] | None = None
    next_event_id: int = 1
    terminal_emit_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def alloc_event_id(self) -> int:
        cur = self.next_event_id
        self.next_event_id = cur + 1
        return cur

    def touch(self) -> None:
        self.last_activity_monotonic = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.last_activity_monotonic) > self.ttl_seconds


class TurnSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, TurnSession] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, turn_id: str, *, ttl_seconds: float) -> TurnSession:
        async with self._lock:
            session = TurnSession(turn_id=turn_id, buffer=TurnBuffer(), ttl_seconds=ttl_seconds)
            self._sessions[turn_id] = session
            return session

    async def get_session(self, turn_id: str) -> TurnSession | None:
        async with self._lock:
            return self._sessions.get(turn_id)

    async def remove_session(self, turn_id: str) -> None:
        async with self._lock:
            self._sessions.pop(turn_id, None)


GLOBAL_TURN_SESSION_STORE = TurnSessionStore()
