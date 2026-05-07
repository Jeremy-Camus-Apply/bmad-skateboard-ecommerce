# skate-assistant-backend

FastAPI + Google ADK backend for the Skate Assistant. Targets Cloud Run gen-2 (deferred — see Story 1.18).

## Local development

```bash
# Install Python 3.12 toolchain (uv handles this)
uv sync

# Run the API on port 8000
uv run uvicorn app.main:app --reload --port 8000

# Smoke checks
curl localhost:8000/v1/health
curl localhost:8000/v1/readiness

# Lint + type check + tests
uv run ruff check
uv run mypy app/
uv run pytest
```

For the full local stack (Postgres, Redis, Firebase emulator), use the repo-root `docker-compose.yml`:

```bash
cd ..
docker compose up backend
```

## Project layout

```
app/
├── main.py              FastAPI app factory, OTel init, request-id middleware
├── config.py            Pydantic Settings (env-driven)
├── dependencies.py      placeholder (Story 1.2+)
├── api/v1/ops.py        /health, /readiness
├── agents/              Story 1.6+
├── compatibility/       Story 1.8
├── models/              Story 1.2 / 1.8
├── services/            Story 1.6+
└── observability/
    ├── tracing.py       OTel + Cloud Trace init
    └── logging.py       Structured JSON logging
tests/
├── unit/
├── integration/
└── eval/                Story 1.16
migrations/              Alembic — initialized; schema lands in Story 1.2
```

## Environment variables

See `.env.example`. Configuration is fully env-driven via Pydantic Settings — no hard-coded paths or secrets.
