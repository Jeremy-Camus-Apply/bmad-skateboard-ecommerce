"""Structured JSON logging — Cloud Logging auto-ingests stdout from Cloud Run."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from app.config import get_settings

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
request_path_ctx: ContextVar[str | None] = ContextVar("request_path", default=None)
request_status_ctx: ContextVar[int | None] = ContextVar("request_status", default=None)
request_duration_ctx: ContextVar[float | None] = ContextVar("request_duration", default=None)


_SEVERITY = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "severity": _SEVERITY.get(record.levelno, record.levelname),
            "message": record.getMessage(),
            "logger": record.name,
        }

        request_id = request_id_ctx.get()
        if request_id is not None:
            payload["request_id"] = request_id

        path = request_path_ctx.get()
        if path is not None:
            payload["path"] = path

        status = request_status_ctx.get()
        if status is not None:
            payload["status"] = status

        duration = request_duration_ctx.get()
        if duration is not None:
            payload["duration_ms"] = round(duration, 2)

        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Replace the root logger handlers with a single JSON-to-stdout handler."""
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(get_settings().log_level)

    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).propagate = False
