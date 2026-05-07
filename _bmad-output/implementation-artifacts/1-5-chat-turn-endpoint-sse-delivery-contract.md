# Story 1.5: Chat Turn Endpoint + SSE Delivery Contract

Status: review

## Story

As the backend service,
I want a versioned chat-turn endpoint with a strict SSE delivery contract,
So that the frontend can consume tokens reliably with ordering, deduplication, and resume semantics.

## Acceptance Criteria

### AC1: Endpoint Authentication and SSE Stream Setup
**Given** the FastAPI service is running  
**When** a POST to `/v1/chat/turn` arrives with a valid Firebase ID token or anonymous session JWT  
**Then** the service authenticates, validates the request body against a Pydantic schema, generates a `turn_id`, and opens an SSE response

### AC2: SSE Event Contract with Monotonic IDs
**Given** an SSE stream is open  
**When** any event is emitted  
**Then** it carries `event_id` (monotonic integer per turn) and `turn_id` (stable per turn) in the payload  
**And** the SSE-native `id:` field is set to `event_id`  
**And** the server emits `: heartbeat` keepalive every 15 seconds during long pauses

### AC3: Stream Reconnection with Last-Event-ID
**Given** the SSE stream drops mid-turn  
**When** the client reconnects with `Last-Event-ID: <id>`  
**Then** the server resumes from `event_id + 1` for that `turn_id`  
**And** turns abandoned > 5 minutes return a documented error code

### AC4: Terminal Event Guarantee (done OR error, never both, never neither)
**Given** an error occurs during a turn  
**When** the orchestrator emits the terminal event  
**Then** the response is exactly one `done` OR one `error` event (never both, never neither)

### AC5: Structured Error Envelope
**Given** any error response  
**When** the structured error envelope is emitted  
**Then** it contains `{ code, message, request_id, retry_after?, details? }` matching HTTP status code semantics from the project-type spec

## Tasks / Subtasks

- [ ] **Task 1: Create Pydantic request/response schemas for chat turn endpoint** (AC: 1, 2, 5)
  - [ ] 1.1: Define `ChatTurnRequest` model with message field, turn context, and validation rules
  - [ ] 1.2: Define SSE event schemas: `TokenEvent`, `RecommendationEvent`, `DoneEvent`, `ErrorEvent` with monotonic `event_id` and stable `turn_id`
  - [ ] 1.3: Define structured error envelope schema matching HTTP status semantics
  - [ ] 1.4: Add unit tests validating schema constraints and JSON serialization
  - [ ] 1.5: Place schemas in `skate-assistant-backend/app/api/v1/schemas.py` or `models/chat.py`

- [ ] **Task 2: Implement Firebase/Anonymous JWT authentication middleware** (AC: 1)
  - [ ] 2.1: Create auth dependency in `app/dependencies.py` that verifies Firebase ID tokens via `firebase-admin` SDK
  - [ ] 2.2: Add anonymous JWT verification using secret from Secret Manager (placeholder for JWT decode logic)
  - [ ] 2.3: Populate `request.state.user_id` (Firebase UID) or `request.state.anon_session_id` after successful verification
  - [ ] 2.4: Return structured 401 error on invalid/expired tokens
  - [ ] 2.5: Add unit tests with mock tokens (valid/expired/invalid cases)

- [ ] **Task 3: Create POST /v1/chat/turn SSE endpoint handler** (AC: 1, 2, 3, 4)
  - [ ] 3.1: Define route in `app/api/v1/chat.py` with auth dependency and Pydantic request validation
  - [ ] 3.2: Generate unique `turn_id` (UUID v4) at request start
  - [ ] 3.3: Use FastAPI's native `EventSourceResponse` (fastapi.sse) with async generator
  - [ ] 3.4: Implement monotonic `event_id` counter per turn
  - [ ] 3.5: Emit placeholder events: initial acknowledgement token, mock recommendation, terminal `done` event
  - [ ] 3.6: Set SSE-native `id:` field to `event_id` on every event
  - [ ] 3.7: Add 15-second heartbeat using `: heartbeat\n\n` keepalive during stream
  - [ ] 3.8: Handle `Last-Event-ID` header for reconnection (resume from `event_id + 1`)
  - [ ] 3.9: Implement 5-minute turn TTL check; return structured error if exceeded
  - [ ] 3.10: Ensure exactly one terminal event (`done` OR `error`, never both)

- [ ] **Task 4: Add turn state management for reconnection support** (AC: 3)
  - [ ] 4.1: Create in-memory turn state store (dict mapping `turn_id` → buffered events)
  - [ ] 4.2: Store all emitted events during turn with their `event_id`
  - [ ] 4.3: On reconnection with `Last-Event-ID`, replay events from `event_id + 1`
  - [ ] 4.4: Expire turn state 5 minutes after last event emission
  - [ ] 4.5: Add unit tests for reconnection logic (happy path, expired turn, out-of-range event_id)

- [ ] **Task 5: Implement structured error handling and logging** (AC: 4, 5)
  - [ ] 5.1: Define error codes enum: `INVALID_REQUEST`, `AUTH_FAILED`, `TURN_EXPIRED`, `INTERNAL_ERROR`
  - [ ] 5.2: Create error response builder that constructs structured envelope with code, message, request_id, retry_after
  - [ ] 5.3: Emit `error` SSE event with structured envelope on any orchestrator failure
  - [ ] 5.4: Log all errors with request_id, turn_id, event_id context using existing structured logging
  - [ ] 5.5: Add unit tests for all error scenarios

- [ ] **Task 6: Add integration tests for complete SSE flow** (AC: 1, 2, 3, 4, 5)
  - [ ] 6.1: Test valid Firebase token → SSE stream → receives events with correct fields
  - [ ] 6.2: Test anonymous JWT → SSE stream → receives events
  - [ ] 6.3: Test invalid token → receives 401 structured error
  - [ ] 6.4: Test stream disconnection → reconnect with `Last-Event-ID` → resume from correct event
  - [ ] 6.5: Test turn expiration (> 5 min) → receives structured error
  - [ ] 6.6: Test error during turn → receives exactly one `error` event, no `done`
  - [ ] 6.7: Test successful turn → receives exactly one `done` event
  - [ ] 6.8: Use httpx async test client with SSE parsing

- [ ] **Task 7: Update CI/CD to verify SSE endpoint** (AC: all)
  - [ ] 7.1: Ensure backend CI runs new integration tests in `.github/workflows/backend-ci.yml`
  - [ ] 7.2: Add health check verification that schema version matches (inherited from Story 1.2)
  - [ ] 7.3: Verify lint/type/test pipeline stays green

## Dev Notes

### Epic Context (from Epic 1)

**Story Position in Epic**  
Story 1.5 is the first conversational-interaction story after infrastructure (1.1, 1.2) and design foundation (1.3). It establishes the HTTP contract that all downstream agent stories (1.6–1.9) will use for streaming responses.

**Critical Dependencies**
- **Upstream:** Story 1.2 (Cloud SQL + Alembic) provides the database foundation, though this story doesn't yet write to it
- **Upstream:** Story 1.1 (project scaffolding) provides FastAPI structure, middleware patterns, and CI baseline
- **Downstream:** Stories 1.6–1.9 (agents) will integrate into this SSE streaming contract
- **Downstream:** Story 1.15 (observability) will add per-trace telemetry hooks to this endpoint

**What This Story DOES NOT Include**
- ❌ No actual LLM calls yet (Story 1.6 IntentAgent is first LLM integration)
- ❌ No database writes yet (session persistence comes in Story 1.4/2.2)
- ❌ No rate limiting yet (Story 1.13)
- ❌ No semantic cache yet (Story 1.14)
- ❌ No Langfuse traces yet (Story 1.15)
- ✅ **This story is ONLY the HTTP endpoint, SSE contract, and auth middleware**

### Previous Story Intelligence (Story 1.2)

**Patterns to Continue from Story 1.2**
- ✅ Use `app/config.py` Pydantic Settings pattern for env-driven config
- ✅ Use structured logging with `request_id_ctx` contextvars (already in `app/main.py`)
- ✅ Use `app/dependencies.py` for FastAPI dependency injection
- ✅ Use strict mypy/ruff/pytest discipline (no type: ignore without justification)
- ✅ Keep `alembic_version` schema check at startup (Story 1.2 pattern)
- ✅ Use asyncpg driver for all database connections

**Key File Structures Established**
- `app/main.py` — Application factory with RequestContextMiddleware, lifespan, exception handlers
- `app/api/v1/ops.py` — Health/readiness endpoints returning schema version
- `app/api/exceptions.py` — Custom exception handlers
- `app/config.py` — Pydantic Settings with env validation
- `app/observability/logging.py` — Structured logging with contextvars (request_id, path, status, duration)
- `app/services/schema_version.py` — Alembic version validation at startup

**Review Findings from Story 1.2 to Preserve**
- ✅ Async engine handling in migrations/env.py was corrected (don't break it)
- ✅ Backend CI intentionally fails loudly on security/reproducibility issues
- ✅ Request-id propagation via middleware + contextvars is working correctly

### Architecture Compliance Requirements

**Technology Stack (from architecture.md)**
- **Language:** Python 3.12
- **Framework:** FastAPI with native SSE support (`fastapi.sse.EventSourceResponse`)
- **Auth:** Firebase Admin SDK (`firebase-admin`) for ID token verification
- **Validation:** Pydantic v2 with strict mode where appropriate
- **Async:** `asyncio` + `asyncpg` for database (though not used in this story yet)
- **Dependency Management:** `uv` package manager (already configured in Story 1.1)

**Code Organization (from architecture.md)**
- **API Handlers:** `app/api/v1/chat.py` — thin routing, Pydantic validation, response shaping (NO business logic)
- **Dependencies:** `app/dependencies.py` — auth middleware, dependency injection
- **Schemas:** `app/api/v1/schemas.py` or `app/models/chat.py` — Pydantic request/response models
- **Services:** Future `app/services/auth.py` may be needed for JWT handling (create if makes sense)

**SSE Delivery Contract (from architecture.md § SSE Contract)**

**Event Types:**
```python
# All events carry turn_id + event_id in payload
# SSE-native id: field = event_id

type: "token"
data: { turn_id, event_id, text: "..." }

type: "recommendation"  
data: { turn_id, event_id, sku, name, price, ... }

type: "done"
data: { turn_id, event_id }

type: "error"
data: { turn_id, event_id, code, message, request_id, retry_after?, details? }

# Heartbeat (SSE comment line, no data payload)
: heartbeat
```

**Event ID Rules:**
- `event_id` is monotonic integer starting at 1 per turn
- `turn_id` is stable UUID v4 for the entire turn
- SSE-native `id:` field must match `event_id` for reconnection to work
- Client reconnects with `Last-Event-ID: N` → server resumes from `N+1`

**Terminal Event Contract:**
- Exactly one of `done` OR `error`, never both, never neither
- On orchestrator success: emit `done` event
- On orchestrator error: emit `error` event with structured envelope
- Stream MUST close after terminal event

**Authentication Flow (from architecture.md § Authentication)**
1. Client sends `Authorization: Bearer <firebase-id-token>` OR `X-Anonymous-Session: <jwt>`
2. FastAPI middleware calls `firebase_admin.auth.verify_id_token()` or custom JWT verify
3. Populate `request.state.user_id` (Firebase UID) or `request.state.anon_session_id`
4. On failure: return structured 401 with error envelope
5. Downstream handlers access `request.state.user_id` or `request.state.anon_session_id` — never raw tokens

**Error Envelope Structure (from architecture.md § Error Handling)**
```python
{
  "code": "TURN_EXPIRED",  # Machine-readable enum
  "message": "Turn abandoned for over 5 minutes",  # Human-readable
  "request_id": "abc-123-def",  # From RequestContextMiddleware
  "retry_after": 60,  # Optional: seconds to wait before retry
  "details": {}  # Optional: structured debug info
}
```

**Failure Mode (from architecture.md § Failure-Mode Matrix)**
- Firebase Auth timeout: 1s soft, 3s hard, 1 retry on transient
- On persistent auth failure: 401 to client, client SDK refreshes token and retries once

### Latest Technical Information (Web Research Snapshot)

**FastAPI SSE Support (2026)**
- ✅ **FastAPI now has NATIVE SSE support** via `fastapi.sse.EventSourceResponse` and `ServerSentEvent` classes
- ✅ Use `response_class=EventSourceResponse` on route with async generator
- ✅ Automatic `Content-Type: text/event-stream`, cache-control headers, keep-alive pings every 15s
- ✅ `ServerSentEvent(data=..., event=..., id=..., retry=...)` for structured events
- ✅ Plain objects (dicts, Pydantic models) are auto-JSON-encoded as `data:` field
- ⚠️ **Disconnect Detection:** Always check `await request.is_disconnected()` before blocking operations
- ⚠️ **Broadcasting Multiple Clients:** Use per-client `asyncio.Queue`, not a single queue

**Alternative Library: sse-starlette**
- `sse-starlette` v3.4.2+ is actively maintained (2026) and W3C-compliant
- Provides custom ping config, multi-threaded support, graceful shutdown
- Consider if native FastAPI SSE is insufficient

**Firebase Admin SDK (2026)**
- ✅ `firebase_admin.auth.verify_id_token(token)` is the primary verification function
- ✅ Returns decoded token dict with `uid`, `email`, etc.
- ✅ Raises `firebase_admin.auth.InvalidIdTokenError`, `ExpiredIdTokenError`, `RevokedIdTokenError`
- ✅ Latest SDK version: 7.4.0 (April 2026) — added phone number verification API (not needed for this story)
- ✅ Requires service account credentials via Secret Manager (already configured in Story 1.1)

**Pydantic v2 Best Practices (2026)**
- ✅ **Strict Mode:** Use `ConfigDict(strict=True)` to reject automatic type coercion in production
- ✅ **Field Constraints:** Use `Field(min_length=..., max_length=..., pattern=...)` instead of custom validators
- ✅ **Cross-Field Validation:** Use `@model_validator(mode='after')` for multi-field checks
- ✅ **Custom Error Responses:** Register FastAPI exception handler for `RequestValidationError` to return standardized JSON
- ✅ Pydantic v2 is 5-50x faster than v1 thanks to Rust-based validation core
- ✅ Use `exclude_unset=True` on `model_dump()` for partial updates (not needed in this story)

### Library Framework Requirements

**Core Dependencies (already in pyproject.toml from Story 1.1)**
- `fastapi[standard]` — includes SSE support as of FastAPI 0.100+
- `firebase-admin` — for Firebase ID token verification
- `pydantic` — v2.x for request/response validation
- `pydantic-settings` — for env-driven config (already used)
- `uvicorn` — ASGI server

**New Dependencies for This Story**
- ✅ `pyjwt` — for anonymous JWT verification (if not already present)
- ✅ `cryptography` — required by `pyjwt` for RSA/EC signatures

**Install Command**
```bash
cd skate-assistant-backend
uv add pyjwt cryptography
```

### File Structure Requirements

**Files to CREATE:**
```
skate-assistant-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py          # NEW: POST /v1/chat/turn SSE endpoint
│   │       └── schemas.py       # NEW: ChatTurnRequest, SSE event schemas, error envelope
│   ├── dependencies.py          # UPDATE: Add auth dependency (verify Firebase/JWT)
│   ├── services/
│   │   └── turn_state.py        # NEW: In-memory turn state for reconnection
│   └── models/
│       └── errors.py            # NEW: Error code enums, structured error builder
├── tests/
│   ├── unit/
│   │   ├── test_chat_schemas.py      # NEW: Schema validation tests
│   │   ├── test_auth_dependency.py   # NEW: Auth middleware unit tests
│   │   └── test_turn_state.py        # NEW: Turn state management tests
│   └── integration/
│       └── test_chat_turn_sse.py     # NEW: Full SSE flow integration tests
```

**Files to UPDATE:**
```
skate-assistant-backend/
├── app/
│   ├── api/v1/__init__.py       # UPDATE: Import and include chat router
│   ├── config.py                # UPDATE: Add JWT signing secret config
│   └── dependencies.py          # UPDATE: Add auth dependency
```

**Files to PRESERVE (do not modify):**
```
skate-assistant-backend/
├── app/
│   ├── main.py                  # Keep RequestContextMiddleware, lifespan, exception handlers
│   ├── api/v1/ops.py           # Keep health/readiness endpoints
│   └── services/schema_version.py  # Keep Alembic version check at startup
├── migrations/                  # Keep existing migrations untouched
└── .github/workflows/backend-ci.yml  # Update only to run new tests
```

### Testing Requirements

**Unit Tests (pytest + httpx test client)**
- ✅ Schema validation: valid/invalid ChatTurnRequest, event schemas
- ✅ Auth dependency: valid/expired/invalid Firebase tokens, anonymous JWT cases
- ✅ Turn state: store/retrieve/expire events, reconnection replay logic
- ✅ Error envelope: structured error builder with all required fields

**Integration Tests (pytest + httpx async client + SSE parsing)**
- ✅ Valid Firebase token → POST /v1/chat/turn → receives SSE stream with events
- ✅ Anonymous JWT → POST /v1/chat/turn → receives SSE stream
- ✅ Invalid token → receives 401 with structured error
- ✅ Stream disconnect → reconnect with `Last-Event-ID` → resumes from correct event
- ✅ Turn expiration (> 5 min) → receives structured error
- ✅ Orchestrator error → receives exactly one `error` event, no `done`
- ✅ Successful turn → receives exactly one `done` event
- ✅ Heartbeat emission during long pauses (mock delay in generator)

**Test Coverage Target**
- ✅ Core SSE flow: 100% coverage
- ✅ Auth dependency: 100% coverage (all token states)
- ✅ Turn state: 100% coverage (store/retrieve/expire/reconnect)
- ✅ Error handling: 100% coverage (all error codes)

### Acceptance Criteria Validation Checklist

Before marking this story as DONE, verify:

- [ ] **AC1:** POST /v1/chat/turn accepts Firebase ID token OR anonymous JWT
- [ ] **AC1:** Request body validated against Pydantic schema
- [ ] **AC1:** Unique `turn_id` (UUID v4) generated per request
- [ ] **AC1:** SSE response opened with `Content-Type: text/event-stream`
- [ ] **AC2:** Every event carries `event_id` (monotonic integer) and `turn_id` in payload
- [ ] **AC2:** SSE-native `id:` field set to `event_id`
- [ ] **AC2:** Heartbeat `: heartbeat` emitted every 15 seconds during pauses
- [ ] **AC3:** Client can reconnect with `Last-Event-ID: N` header
- [ ] **AC3:** Server resumes stream from `event_id N+1`
- [ ] **AC3:** Turns abandoned > 5 minutes return structured error
- [ ] **AC4:** On error: exactly one `error` event, no `done`
- [ ] **AC4:** On success: exactly one `done` event
- [ ] **AC5:** Error envelope includes: code, message, request_id, optional retry_after and details
- [ ] All unit tests pass (schema, auth, turn state, error handling)
- [ ] All integration tests pass (SSE flow, auth, reconnection, expiration, terminal events)
- [ ] Backend CI green (lint, type, test, security)
- [ ] Code review completed with no blocking issues

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` § Story 1.5 — Acceptance Criteria]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § SSE Delivery Contract]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Authentication Flow]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Error Envelope Structure]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Failure-Mode Matrix — Firebase Auth]
- [Source: `_bmad-output/implementation-artifacts/1-2-cloud-sql-provisioning-alembic-initial-schema-ci-gate.md` — Previous story patterns]
- [Web Research: FastAPI SSE Support 2026 — Native EventSourceResponse]
- [Web Research: Firebase Admin SDK 2026 — verify_id_token() patterns]
- [Web Research: Pydantic v2 Best Practices 2026 — Strict mode, Field constraints]

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent_

### Completion Notes List

_To be filled by dev agent as tasks are completed_

### File List

**Modified:**
_To be filled by dev agent_

**New:**
_To be filled by dev agent_

## Change Log

- 2026-05-07: Story file created by context engine with comprehensive architecture and web research analysis
