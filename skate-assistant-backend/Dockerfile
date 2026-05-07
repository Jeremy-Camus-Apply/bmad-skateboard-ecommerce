# syntax=docker/dockerfile:1.7

# ── Build stage ──────────────────────────────────────────────────
FROM python:3.12-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/build/.venv

WORKDIR /build

# uv version pinned to match local + CI (kept in sync via .github/workflows/backend-ci.yml).
RUN pip install --no-cache-dir "uv==0.5.11"

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ── Runtime stage ────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN useradd --uid 10001 --no-create-home --shell /bin/false appuser

WORKDIR /app

COPY --from=build /build/.venv /app/.venv
COPY --from=build /build/app /app/app

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/v1/health', timeout=3).read()" || exit 1

# --timeout-graceful-shutdown caps the wait for in-flight SSE requests on SIGTERM.
# Cloud Run's default termination grace is 10s; 30s is the safe ceiling.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-graceful-shutdown", "30"]
