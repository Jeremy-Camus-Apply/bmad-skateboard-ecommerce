"""Shared test helpers."""

from __future__ import annotations

import json
import time

import jwt


def mint_anonymous_session_jwt(
    *,
    secret: str,
    sub: str = "anon-unit-test-session",
) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": sub, "iat": now, "exp": now + 3600},
        secret,
        algorithm="HS256",
    )


def parse_sse_blocks(body: str) -> list[dict[str, str]]:
    """Parse a minimal subset of SSE framing from a decoded response body."""

    blocks: list[dict[str, str]] = []
    for raw in body.split("\n\n"):
        block = raw.strip()
        if not block:
            continue
        if block.startswith(":"):
            blocks.append({"comment": block})
            continue

        evt: dict[str, str] = {}
        for line in block.split("\n"):
            if line.startswith("id:"):
                evt["id"] = line.removeprefix("id:").strip()
            elif line.startswith("event:"):
                evt["event"] = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                evt["data"] = line.removeprefix("data:").strip()
        blocks.append(evt)
    return blocks


def sse_events(blocks: list[dict[str, str]]) -> list[dict[str, str]]:
    return [b for b in blocks if "event" in b]


def json_data(block: dict[str, str]) -> dict[str, object]:
    return json.loads(block["data"])
