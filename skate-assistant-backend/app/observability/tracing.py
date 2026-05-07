"""OpenTelemetry tracing — Cloud Trace exporter on GCP, console exporter locally."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

_initialized = False


def _build_exporter() -> SpanExporter | None:
    settings = get_settings()
    if settings.otel_traces_exporter == "gcp_trace":
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

            return CloudTraceSpanExporter(  # type: ignore[no-untyped-call]
                project_id=settings.google_cloud_project
            )
        except ImportError:
            logger.warning(
                "gcp_trace exporter requested but exporter package missing; "
                "falling back to console exporter"
            )
            return ConsoleSpanExporter()
        except Exception:
            logger.exception("gcp_trace exporter init failed; falling back to console exporter")
            return ConsoleSpanExporter()
    if settings.otel_traces_exporter == "console":
        return ConsoleSpanExporter()
    # otel_traces_exporter == "none"
    return None


def init_tracing(app: FastAPI) -> TracerProvider | None:
    """Wire OTel TracerProvider with the configured exporter and instrument FastAPI.

    Returns the provider so the lifespan can shut it down on exit.
    Idempotent: subsequent calls are no-ops (logged once at debug).
    """
    global _initialized
    if _initialized:
        logger.debug("init_tracing called more than once; ignoring")
        return None

    settings = get_settings()
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.git_commit_sha,
            "deployment.environment": settings.environment,
        }
    )
    provider = TracerProvider(resource=resource)

    exporter = _build_exporter()
    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    _initialized = True
    return provider


def reset_tracing_for_tests() -> None:
    """Test-only helper to reset the idempotency flag."""
    global _initialized
    _initialized = False
