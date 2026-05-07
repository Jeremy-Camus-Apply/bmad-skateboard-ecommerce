"""Structured-error-envelope exception handlers.

Every error response follows the Architecture-mandated shape:

    { "code": str, "message": str, "request_id": str,
      "retry_after"?: int, "details"?: dict | list }

`request_id` is sourced from `request.state.request_id` populated by the
RequestContextMiddleware. Handlers also stamp `X-Request-Id` on the response
so error paths preserve the same correlation guarantee as success paths.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _envelope(
    code: str,
    message: str,
    request_id: str,
    *,
    retry_after: int | None = None,
    details: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }
    if retry_after is not None:
        payload["retry_after"] = retry_after
    if details is not None:
        payload["details"] = details
    return payload


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = _request_id(request)
    response = JSONResponse(
        status_code=exc.status_code,
        content=_envelope(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail) if exc.detail else "HTTP error",
            request_id=request_id,
        ),
    )
    if request_id:
        response.headers["X-Request-Id"] = request_id
    return response


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = _request_id(request)
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_envelope(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            request_id=request_id,
            details=exc.errors(),
        ),
    )
    if request_id:
        response.headers["X-Request-Id"] = request_id
    return response


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = _request_id(request)
    logger.exception("unhandled_exception", extra={"request_id": request_id})
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope(
            code="INTERNAL_ERROR",
            message="Internal server error",
            request_id=request_id,
        ),
    )
    if request_id:
        response.headers["X-Request-Id"] = request_id
    return response


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)
