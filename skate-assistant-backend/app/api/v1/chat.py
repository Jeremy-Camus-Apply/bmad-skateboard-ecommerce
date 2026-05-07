"""`POST /v1/chat/turn` — SSE streaming scaffolding (Story 1.5).

FastAPI 0.115.x does not ship `fastapi.sse`; SSE framing is implemented via
`StreamingResponse` + explicit `text/event-stream` encoding.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.responses import StreamingResponse

from app.api.v1.schemas import ChatTurnRequest, ErrorEventPayload
from app.config import Settings, get_settings
from app.dependencies import require_chat_principal
from app.models.errors import ChatErrorCode
from app.services.turn_state import (
    GLOBAL_TURN_SESSION_STORE,
    BufferedSseEvent,
    TurnSession,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat")

_HEARTBEAT_BYTES = b": heartbeat\n\n"


def _encode_sse(*, event_id: int, event_name: str | None, data: dict[str, Any]) -> bytes:
    lines: list[str] = []
    lines.append(f"id: {event_id}")
    if event_name:
        lines.append(f"event: {event_name}")
    lines.append(f"data: {json.dumps(data, separators=(',', ':'), sort_keys=True)}")
    lines.append("")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def _parse_last_event_id(request: Request) -> int:
    raw = request.headers.get("last-event-id")
    if raw is None or raw.strip() == "":
        return 0
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Last-Event-ID header",
        ) from exc
    if value < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Last-Event-ID header",
        )
    return value


async def _append_sse_event(
    session: TurnSession, event_name: str, data_extra: dict[str, Any]
) -> BufferedSseEvent:
    event_id = session.alloc_event_id()
    data: dict[str, Any] = {"turn_id": session.turn_id, "event_id": event_id, **data_extra}
    evt = BufferedSseEvent(event_id=event_id, event_name=event_name, data=data)
    await session.buffer.append(evt)
    session.touch()
    return evt


async def _append_terminal_error_event(
    *,
    session: TurnSession,
    request_id: str,
    code: ChatErrorCode,
    message: str,
    retry_after: int | None = None,
    details: dict[str, Any] | list[Any] | None = None,
) -> None:
    event_id = session.alloc_event_id()
    payload = ErrorEventPayload(
        turn_id=session.turn_id,
        event_id=event_id,
        code=code.value,
        message=message,
        request_id=request_id,
        retry_after=retry_after,
        details=details,
    ).model_dump(mode="json")
    await session.buffer.append(
        BufferedSseEvent(event_id=event_id, event_name="error", data=payload)
    )
    session.touch()


async def run_placeholder_turn(*, session: TurnSession, request: Request, message: str) -> None:
    """Emit a deterministic placeholder sequence (Story 1.6+ replaces this body)."""

    _ = message  # referenced by future orchestrator wiring
    request_id = getattr(request.state, "request_id", "")
    try:
        await _append_sse_event(
            session, "token", {"text": "Got it — pulling some setups for that."}
        )
        await asyncio.sleep(0)  # yield control; keeps streaming tests meaningful
        await _append_sse_event(
            session,
            "recommendation",
            {"sku": "MOCK-001", "name": "Mock Complete Setup", "price_cents": 9999},
        )
        await _append_sse_event(session, "done", {})
    except Exception as exc:  # pragma: no cover — defensive guardrail
        logger.exception("placeholder_turn_failed", extra={"turn_id": session.turn_id})
        await _append_terminal_error_event(
            session=session,
            request_id=request_id,
            code=ChatErrorCode.INTERNAL_ERROR,
            message="Internal server error",
            details={"error": str(exc)},
        )


def _start_turn_task_if_needed(*, session: TurnSession, request: Request, message: str) -> None:
    if session.buffer.terminal_kind is not None:
        return
    if session.task is not None and not session.task.done():
        return
    session.task = asyncio.create_task(
        run_placeholder_turn(session=session, request=request, message=message),
    )


async def _maybe_emit_turn_expired(*, session: TurnSession, request_id: str) -> None:
    async with session.terminal_emit_lock:
        if session.buffer.terminal_kind is not None:
            return
        if not session.is_expired():
            return
        await _append_terminal_error_event(
            session=session,
            request_id=request_id,
            code=ChatErrorCode.TURN_EXPIRED,
            message="Turn abandoned for over 5 minutes",
        )


async def sse_byte_stream(
    *,
    session: TurnSession,
    settings: Settings,
    request: Request,
    resume_after_id: int,
) -> AsyncIterator[bytes]:
    request_id = getattr(request.state, "request_id", "")
    buffer = session.buffer
    heartbeat_s = settings.chat_turn_heartbeat_seconds

    last_id = resume_after_id

    while True:
        await _maybe_emit_turn_expired(session=session, request_id=request_id)

        pending = buffer.snapshot_after(last_id)
        if pending:
            for evt in pending:
                yield _encode_sse(event_id=evt.event_id, event_name=evt.event_name, data=evt.data)
                last_id = evt.event_id
                if evt.event_name in ("done", "error"):
                    return
            continue

        if buffer.terminal_kind is not None:
            return

        try:
            next_evt = await asyncio.wait_for(buffer.wait_next_after(last_id), timeout=heartbeat_s)
        except TimeoutError:
            yield _HEARTBEAT_BYTES
            continue

        if next_evt is None:
            return

        yield _encode_sse(
            event_id=next_evt.event_id, event_name=next_evt.event_name, data=next_evt.data
        )
        last_id = next_evt.event_id
        if next_evt.event_name in ("done", "error"):
            return


async def _expired_turn_stream(*, turn_id: str, request_id: str) -> AsyncIterator[bytes]:
    payload = ErrorEventPayload(
        turn_id=turn_id,
        event_id=1,
        code=ChatErrorCode.TURN_EXPIRED.value,
        message="Turn abandoned for over 5 minutes",
        request_id=request_id,
    ).model_dump(mode="json")
    yield _encode_sse(event_id=1, event_name="error", data=payload)


@router.post("/turn")
async def chat_turn(
    request: Request,
    body: ChatTurnRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[None, Depends(require_chat_principal)],
) -> StreamingResponse:
    last_event_id = _parse_last_event_id(request)
    store = GLOBAL_TURN_SESSION_STORE

    if body.turn_id is None:
        turn_id = str(uuid.uuid4())
        session = await store.create_session(turn_id, ttl_seconds=settings.chat_turn_ttl_seconds)
        session.touch()
        _start_turn_task_if_needed(session=session, request=request, message=body.message)
        stream = sse_byte_stream(
            session=session,
            settings=settings,
            request=request,
            resume_after_id=last_event_id,
        )
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    resume_session = await store.get_session(str(body.turn_id))
    if resume_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown chat turn")

    request_id = getattr(request.state, "request_id", "")
    if resume_session.is_expired():
        return StreamingResponse(
            _expired_turn_stream(turn_id=resume_session.turn_id, request_id=request_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    _start_turn_task_if_needed(session=resume_session, request=request, message=body.message)
    stream = sse_byte_stream(
        session=resume_session,
        settings=settings,
        request=request,
        resume_after_id=last_event_id,
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
