"""FastAPI application factory + request-id middleware + observability wiring."""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import Token

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.v1 import router as v1_router
from app.config import get_settings
from app.observability import configure_logging, init_tracing
from app.observability.logging import (
    request_duration_ctx,
    request_id_ctx,
    request_path_ctx,
    request_status_ctx,
)
from app.services.schema_version import validate_schema_compatibility

logger = logging.getLogger(__name__)

# Bound + validated incoming X-Request-Id. Anything else is replaced with a fresh UUID.
_REQUEST_ID_MAX_LEN = 128
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _coerce_request_id(incoming: str | None) -> str:
    if not incoming:
        return str(uuid.uuid4())
    if len(incoming) > _REQUEST_ID_MAX_LEN:
        return str(uuid.uuid4())
    if not _REQUEST_ID_PATTERN.fullmatch(incoming):
        return str(uuid.uuid4())
    return incoming


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Generate/honor a request_id, propagate via contextvars and X-Request-Id header.

    Also stamps the request_id as a span attribute on the current span so that
    Cloud Trace ↔ Cloud Logging correlation works without an out-of-band step.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _coerce_request_id(request.headers.get("x-request-id"))

        token_id: Token[str | None] | None = None
        token_path: Token[str | None] | None = None
        token_status: Token[int | None] | None = None
        token_duration: Token[float | None] | None = None

        token_id = request_id_ctx.set(request_id)
        token_path = request_path_ctx.set(request.url.path)
        token_status = request_status_ctx.set(None)
        token_duration = request_duration_ctx.set(None)

        request.state.request_id = request_id

        # Stamp request_id on the active span (FastAPIInstrumentor created it).
        try:
            from opentelemetry import trace as _trace

            current_span = _trace.get_current_span()
            if current_span is not None:
                current_span.set_attribute("request_id", request_id)
        except Exception:  # pragma: no cover — never block requests on observability
            logger.debug("could not stamp request_id on span", exc_info=True)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            request_duration_ctx.set(elapsed_ms)
            request_status_ctx.set(500)
            logger.exception("unhandled_exception")
            raise
        else:
            elapsed_ms = (time.perf_counter() - start) * 1000
            request_status_ctx.set(response.status_code)
            request_duration_ctx.set(elapsed_ms)
            response.headers["X-Request-Id"] = request_id
            logger.info("request_completed")
            return response
        finally:
            if token_id is not None:
                request_id_ctx.reset(token_id)
            if token_path is not None:
                request_path_ctx.reset(token_path)
            if token_status is not None:
                request_status_ctx.reset(token_status)
            if token_duration is not None:
                request_duration_ctx.reset(token_duration)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    provider = init_tracing(app)
    applied_schema = await validate_schema_compatibility()
    logger.info("schema_validation_passed", extra={"schema_version": applied_schema})
    logger.info("startup_complete")
    try:
        yield
    finally:
        if provider is not None:
            try:
                provider.shutdown()
            except Exception:
                logger.exception("provider_shutdown_failed")
        logger.info("shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="skate-assistant-backend",
        version=settings.git_commit_sha,
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    app.include_router(v1_router)
    return app


app = create_app()
