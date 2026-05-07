# Story 1.1: Project Foundation & GCP Infrastructure

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **development team**,
I want **the project scaffolded with all required GCP infrastructure provisioned via Terraform, both frontend and backend services running and deployable, GitHub Actions CI/CD configured, and observability emitting traces and logs to GCP**,
so that **every subsequent story builds on a verified, reproducible foundation rather than re-litigating infrastructure decisions**.

## Acceptance Criteria

**AC1 — GCP foundation provisioned via Terraform**

- **Given** a new GCP project with billing enabled
- **When** Terraform plan and apply runs from the IaC repository
- **Then** VPC + subnet, Secret Manager, Artifact Registry, and per-purpose IAM service accounts (`cloud-run-runtime`, `ci`, `migration-job`) exist with **least-privilege** role bindings documented
- **And** Terraform state is stored in a managed GCS backend with object versioning enabled and state-locking via the GCS lock mechanism

**AC2 — Frontend + backend scaffolds build and deploy**

- **Given** the GCP foundation is provisioned
- **When** `pnpm create next-app` (frontend) and `uv init` + FastAPI + ADK scaffolds (backend) complete
- **Then** both projects build cleanly with zero TypeScript / ESLint errors (frontend) and zero ruff / mypy errors (backend)
- **And** the frontend deploys successfully to Vercel preview
- **And** the backend deploys successfully to Cloud Run staging
- **And** `/health` and `/readiness` endpoints return HTTP 200 with structured JSON `{ "status": "ok", "version": "<commit-sha>", "schema_version": "<alembic-rev>" }`

**AC3 — GitHub Actions CI/CD pipeline gates merges**

- **Given** the projects exist and are pushed to GitHub
- **When** a PR is opened against `main`
- **Then** the CI pipeline runs **lint** (ruff backend / ESLint frontend) → **typecheck** (mypy backend / `tsc --strict` frontend) → **container build** → **vulnerability scan** (Trivy or equivalent) → **staging deploy**
- **And** any failure blocks merge via branch protection rules

**AC4 — Observability emits traces and logs to GCP from request 1**

- **Given** the deployed staging service
- **When** any HTTP request hits the backend
- **Then** a trace with a unique `request_id` appears in **Cloud Trace** within 60 seconds
- **And** a structured JSON log entry appears in **Cloud Logging** with `request_id`, `path`, `status`, `duration_ms` fields (no raw stack traces)

## Tasks / Subtasks

> **Scope note (set with user, 2026-05-07):** local-first this pass. No
> `terraform apply`, no Cloud Run / Vercel deploy, no GitHub branch-protection
> changes, no live cloud verification. Subtasks marked **(deferred — cloud)**
> are coded as artifacts but await platform-team coordination + credentials.

- [x] **Task 1: Initialize Terraform IaC repository** (AC: 1) — _code complete; apply deferred_
  - [x] Subtask 1.1: Create `infra/` directory at the project root with `terraform/` subdirectory; commit a `.gitignore` excluding `.terraform/`, `*.tfstate*`, `*.tfvars` (except example).
  - [ ] **(deferred — cloud)** Subtask 1.2: Create a GCS bucket `<project-id>-terraform-state` with **object versioning enabled**; configure as Terraform state backend in `terraform/backend.tf`. _Backend code in `infra/terraform/backend.tf` ready; bucket creation deferred._
  - [x] Subtask 1.3: Define GCP provider in `terraform/main.tf` with project, region (`us-central1` default — confirm in `terraform.tfvars.example`), and credentials via Application Default Credentials.
  - [x] Subtask 1.4: Create Terraform module `terraform/modules/network/` provisioning a VPC + private subnet (`/24`) for Cloud Run + Cloud SQL connectivity. Include VPC connector for Cloud Run egress.
  - [x] Subtask 1.5: Create Terraform module `terraform/modules/secrets/` enabling Secret Manager API; pre-create empty placeholder secrets: `firebase-admin-credentials`, `anthropic-api-key`, `langfuse-api-key`, `anonymous-jwt-signing-secret`. _Rotation policies intentionally not set — confirm cadence per intake before apply._
  - [x] Subtask 1.6: Create Terraform module `terraform/modules/artifact-registry/` provisioning an Artifact Registry **Docker repository** named `skate-assistant-backend` in the chosen region. _Includes cleanup policies (keep-last-10, delete-untagged-after-7d)._
  - [x] Subtask 1.7: Create Terraform module `terraform/modules/iam/` provisioning three service accounts: `cloud-run-runtime`, `ci`, `migration-job`; bind only the minimum roles each needs (see *IAM Role Matrix* in Dev Notes). _`migration-job` cloudsql.client binding deferred to Story 1.2 per the matrix note._
  - [ ] **(deferred — cloud)** Subtask 1.8: Run `terraform plan` against staging; review output; run `terraform apply`; verify all resources via `gcloud` CLI.

- [x] **Task 2: Scaffold frontend project** (AC: 2) — _scaffold complete; full shadcn primitive set partial (see Completion Notes)_
  - [x] Subtask 2.1: Equivalent of `pnpm create next-app@latest skate-assistant-frontend --typescript --tailwind --app --src-dir --import-alias "@/*"` — authored manually to a clean Next.js 15 + Tailwind + App Router layout. _Variance documented in Completion Notes._
  - [x] Subtask 2.2: Initialize shadcn/ui — `components.json`, slate-base CSS variables, `cn()` util, tailwind theme tokens.
  - [ ] **(partial)** Subtask 2.3: Install starter component set. _Currently only `Button` is in `src/components/ui/`. Pipeline verified end-to-end (build + lint + tests). Run `pnpm dlx shadcn@latest add input dialog sheet toast tabs tooltip popover accordion skeleton scroll-area avatar badge card switch select separator dropdown-menu` to populate the rest — kept lean here so the foundation PR is reviewable. Blocks no downstream story (Story 1.4 adds Input + Sheet on first need)._ **Do NOT** customize tokens yet (Story 1.3).
  - [x] Subtask 2.4: Add Firebase client SDK + testing deps (`@axe-core/playwright`, `@playwright/test`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`).
  - [x] Subtask 2.5: Add `next.config.ts` configuration: Turbopack for dev (`pnpm dev --turbopack`), `images.remotePatterns` placeholder. _`output: 'standalone'` left default — Vercel handles output natively._
  - [x] Subtask 2.6: `src/app/page.tsx` imports `<Button>` to verify the component pipeline.
  - [x] Subtask 2.7: `pnpm build`, `pnpm lint`, `pnpm typecheck`, `pnpm test:unit` all succeed with zero errors.

- [x] **Task 3: Scaffold backend project** (AC: 2)
  - [x] Subtask 3.1: Initialize Python 3.12 project with `uv` (uv 0.11.7); pyproject targets `requires-python = "==3.12.*"`. _Sibling-repo wording in original story interpreted as monorepo subdir per user direction._
  - [x] Subtask 3.2: All core runtime deps added. **`google-adk==1.5.0`** pinned explicitly with `verified 2026-05-07` comment in `pyproject.toml`. **`anthropic==0.40.0`** also pinned `==`. _ADK 1.5.0 forced uvicorn ≥ 0.34 (transitive constraint); pyproject reflects this._
  - [x] Subtask 3.3: Dev deps via dependency group `dev`: pytest, pytest-asyncio, httpx, ruff, mypy, pre-commit, pytest-cov.
  - [x] Subtask 3.4: Project structure created with `__init__.py` + docstrings in every package: `app/{api/v1,agents,compatibility,models,services,observability}` + `tests/{unit,integration,eval}`.
  - [x] Subtask 3.5: `app/main.py` — `create_app()` factory, OpenTelemetry init in lifespan, graceful shutdown logging.
  - [x] Subtask 3.6: `app/config.py` — Pydantic Settings, env-driven, Literal validation on `environment`/`log_level`/`otel_traces_exporter`. Secret references stored as paths, never values.
  - [x] Subtask 3.7: `app/api/v1/ops.py` — `GET /health` + `GET /readiness` returning `{status, version, schema_version}` with `schema_version=None` per design (Story 1.2 fills it).
  - [x] Subtask 3.8: Router wired under `/v1/` via `app/api/v1/__init__.py`.
  - [x] Subtask 3.9: Multi-stage `Dockerfile` — `python:3.12-slim` build + runtime, non-root `appuser` UID 10001, healthcheck on `/v1/health`, `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]`. _Healthcheck path corrected to `/v1/health` to match actual route prefix._
  - [x] Subtask 3.10: `.dockerignore` excludes git/.venv/tests/__pycache__/.env*.
  - [x] Subtask 3.11: `uv sync` resolves clean. `uv run ruff check` ✅, `uv run ruff format --check .` ✅, `uv run mypy app/` ✅ (strict, 14 source files), `uv run pytest -q` ✅ (4 tests pass).

- [x] **Task 4: GitHub Actions CI/CD pipeline** (AC: 3) — _CI workflows authored; live integration deferred_
  - [x] Subtask 4.1: `.github/workflows/backend-ci.yml` — checkout, uv install, `uv sync`, `ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/unit`, container build (load locally), Trivy scan. **Deploy steps commented out** with full bodies ready to enable when WIF lands.
  - [x] Subtask 4.2: `.github/workflows/frontend-ci.yml` — checkout, pnpm install --frozen-lockfile, lint, typecheck, vitest, `pnpm build`. Vercel deploy handled by Vercel's GitHub integration (no workflow step needed).
  - [x] Subtask 4.3: Trivy step uses `aquasecurity/trivy-action@0.28.0` with `severity: CRITICAL,HIGH`, `exit-code: 1`, `ignore-unfixed: true`.
  - [x] **(code only)** Subtask 4.4: WIF binding code in `infra/github/workload-identity.tf`. Apply step deferred until repo is identified + GCP project provisioned.
  - [ ] **(deferred — GitHub admin)** Subtask 4.5: Configure GitHub branch protection on `main`.
  - [ ] **(deferred — cloud)** Subtask 4.6: Open a sample PR to verify workflows.

- [x] **Task 5: Observability foundation** (AC: 4) — _local emission verified; Cloud Trace verification deferred_
  - [x] Subtask 5.1: `app/observability/tracing.py` — `init_tracing(app)` with TracerProvider + BatchSpanProcessor + CloudTraceSpanExporter (gated on `otel_traces_exporter=gcp_trace`) + ConsoleSpanExporter fallback for local dev. `FastAPIInstrumentor.instrument_app(app)` after creation.
  - [x] Subtask 5.2: `app/observability/logging.py` — JSON formatter on stdout emitting `{timestamp, severity, message, logger, request_id, path, status, duration_ms}`. Uvicorn-access log noise silenced.
  - [x] Subtask 5.3: `RequestContextMiddleware` in `app/main.py` — generates UUID v4 (or honors incoming `X-Request-Id`), sets it on `request.state.request_id`, propagates via contextvars to all log lines + returns it as `X-Request-Id` response header. Verified by smoke tests `test_request_id_is_returned_in_header` and `test_request_id_is_propagated_when_provided`.
  - [ ] **(deferred — cloud)** Subtask 5.4: Deploy + verify trace appears in Cloud Trace within 60s + structured log in Cloud Logging.

- [~] **Task 6: Deploy and verify end-to-end** (AC: 1, 2, 3, 4) — _all deferred except docs_
  - [ ] **(deferred — cloud)** Subtask 6.1: Run `terraform apply` against staging.
  - [ ] **(deferred — cloud)** Subtask 6.2: Push backend image; deploy Cloud Run revision.
  - [ ] **(deferred — cloud)** Subtask 6.3: Push frontend to Vercel preview.
  - [ ] **(deferred — cloud)** Subtask 6.4: Curl `https://<staging-url>/v1/health` and `/v1/readiness`.
  - [ ] **(deferred — cloud)** Subtask 6.5: Open sample PR; verify CI gates merge.
  - [ ] **(deferred — cloud)** Subtask 6.6: Verify trace IDs in Cloud Trace + log entries in Cloud Logging.
  - [x] Subtask 6.7: `docs/deploy.md` — local stack table (host/container ports), where logs/traces show up locally, full cloud apply order, Cloud Run service config baseline, cross-team coordination checklist.

- [x] **Task 7 (added scope, user-requested): Local development orchestration**
  - [x] Subtask 7.1: `docker-compose.yml` at repo root — postgres (pgvector/pgvector:pg16), redis 7, firebase emulator (auth + firestore + UI), backend, frontend. Healthchecks + dependency ordering.
  - [x] Subtask 7.2: `firebase.json`, `.firebaserc`, permissive local `firestore.rules`. Auth on 9099, Firestore on 8080, UI on 4000.
  - [x] Subtask 7.3: Alembic init scaffolding — `alembic.ini`, `migrations/env.py` (async, `target_metadata=None` placeholder), `migrations/script.py.mako`. **No migration files** — schema lands in Story 1.2.
  - [x] Subtask 7.4: `.pre-commit-config.yaml` — ruff (backend), mypy (backend, strict), prettier (frontend), gitleaks (repo-wide), generic hygiene hooks. Install with `uvx pre-commit install`.

## Dev Notes

**This is the foundation story. Every subsequent story builds on what is established here. Conservatism over expedience — extra boundaries, more typed schemas, more observability — is the correct bias.**

### Architecture references (canonical sources for this story)

- **`_bmad-output/planning-artifacts/architecture.md` § Starter Template Evaluation** — full scaffolding command set for both projects, library list, and project structure trees. Treat this as the literal contract for which deps to install and which directories to create.
- **`architecture.md` § Core Architectural Decisions → Infrastructure & Deployment** — Cloud Run gen-2 backend, Vercel frontend, GitHub Actions CI, Terraform IaC. Confirms tooling choices.
- **`architecture.md` § Project Structure & Boundaries** — full backend + frontend directory trees. Do not deviate.
- **`architecture.md` § Architecture Validation Results / Failure-Mode Matrix** — per-dependency timeout / retry / circuit-breaker semantics. Not implemented in this story but referenced in observability scaffolding.
- **PRD § Project-Type Specific Requirements → Backend (Python Service)** — endpoint surface for the operational endpoints `/health`, `/readiness`. Use the structured-error-envelope pattern even on success.

### What this story does NOT do (explicit out-of-scope)

These belong to subsequent stories — **do not implement them in 1.1**:

- ❌ **Cloud SQL provisioning + Alembic initial migration** → Story 1.2.
- ❌ **Tailwind design tokens, Geist fonts, Storybook, axe-core integration** → Story 1.3.
- ❌ **Anonymous session JWT, Firebase Auth client SDK init, ChatInput component** → Story 1.4.
- ❌ **`/v1/chat/turn` SSE endpoint, event_id/turn_id contract** → Story 1.5.
- ❌ **Any agent code, LLM provider clients, Compatibility Layer** → Story 1.6+.
- ❌ **Memorystore Redis, semantic cache, rate limiting** → Story 1.13 / 1.14.
- ❌ **Langfuse self-hosted** → Story 1.15 (but OpenTelemetry to Cloud Trace ships now).

The `schema_version` field in `/health` returns `null` here because there is no Alembic version yet; Story 1.2 fills it. Make sure the JSON shape already exists so 1.2 is purely additive.

### Project structure to create

**Backend** (`skate-assistant-backend/`) — initial structure for this story:

```
skate-assistant-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory, OTel init, request-id middleware
│   ├── config.py            # Pydantic Settings (env-driven)
│   ├── dependencies.py      # placeholder (auth/db deps in later stories)
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── ops.py       # /health, /readiness
│   ├── agents/              # empty package; populated in Story 1.6+
│   │   └── __init__.py
│   ├── compatibility/       # empty package; populated in Story 1.8
│   │   └── __init__.py
│   ├── models/              # empty package; populated in Story 1.2 / 1.8
│   │   └── __init__.py
│   ├── services/            # empty package; populated in Story 1.6+
│   │   └── __init__.py
│   └── observability/
│       ├── __init__.py
│       ├── tracing.py       # OTel + Cloud Trace init
│       └── logging.py       # structured JSON logging
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── eval/                # populated in Story 1.16
│       └── .gitkeep
├── migrations/              # empty Alembic dir; initialized in Story 1.2
├── Dockerfile
├── .dockerignore
├── pyproject.toml
├── uv.lock
└── .env.example
```

**Frontend** (`skate-assistant-frontend/`) — initial structure (most of the directory expansion happens in Stories 1.3, 1.4, 1.10–1.12; Story 1.1 just sets up the canonical Next.js + shadcn skeleton):

```
skate-assistant-frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # default Next.js layout
│   │   ├── page.tsx         # minimal landing — imports a shadcn Button to verify pipeline
│   │   └── globals.css
│   ├── components/
│   │   └── ui/              # shadcn primitives (Button, Input, Dialog, Sheet, ...)
│   └── lib/
│       └── .gitkeep         # populated in Story 1.4+
├── public/
├── tests/                   # populated in Story 1.3+
│   └── .gitkeep
├── tailwind.config.ts       # default; tokens added in Story 1.3
├── next.config.ts
├── package.json
└── pnpm-lock.yaml
```

**Infrastructure** (`infra/`) — co-located in the repository root or its own monorepo location, your choice:

```
infra/
├── terraform/
│   ├── backend.tf           # GCS state backend
│   ├── main.tf              # provider config
│   ├── variables.tf
│   ├── terraform.tfvars.example
│   └── modules/
│       ├── network/         # VPC, subnet, VPC connector
│       ├── secrets/         # Secret Manager + placeholder secrets
│       ├── artifact-registry/
│       └── iam/             # service accounts + role bindings
└── github/
    └── workload-identity.tf # OIDC binding for GitHub-to-GCP keyless auth
```

### IAM Role Matrix (least-privilege bindings to provision in Subtask 1.7)

| Service Account | Roles to grant (minimum) | Scope |
|---|---|---|
| `cloud-run-runtime` | `roles/secretmanager.secretAccessor`, `roles/cloudtrace.agent`, `roles/logging.logWriter`, `roles/monitoring.metricWriter` | Project |
| `ci` | `roles/artifactregistry.writer`, `roles/run.developer`, `roles/iam.serviceAccountUser` (on `cloud-run-runtime`) | Project / specific SA |
| `migration-job` | `roles/cloudsql.client` (Story 1.2 binding — define the SA now, leave binding for Story 1.2) | Project |

**Do NOT grant `roles/owner`, `roles/editor`, or `roles/iam.serviceAccountAdmin` to any of these accounts.** If a role you need does not exist in this matrix, escalate before adding it.

### Library version pinning guidance

ADK is the highest-risk pin per Architecture risk mitigation. **At scaffolding time, verify the current stable `google-adk` version**, pin it explicitly in `pyproject.toml`, and document the version + verification date in a `pyproject.toml` comment. If the current ADK version has known production issues, defer to LangGraph as documented in the Architecture ADR.

For all other libraries, pin to current stable major.minor (caret-style in pyproject is fine for non-critical deps; explicit `==` for ADK and Anthropic SDK to avoid surprise breakage).

### Cloud Run service config (baseline — tuned in Story 1.18)

For staging deploy in this story, use these conservative baselines:

- **Execution environment:** **gen-2** (required — supports up to 60-min request timeouts for SSE in later stories)
- **CPU:** 2 vCPU
- **Memory:** 4 GiB
- **Concurrency per instance:** 40
- **Min instances:** 0 (staging — cost-conscious; production will be min-2 in Story 1.18)
- **Max instances:** 10 (staging — production is 50)
- **Request timeout:** 60 minutes (gen-2 max)
- **VPC connector:** attached, all egress (required for later Cloud SQL private-IP access in Story 1.2)
- **Service account:** `cloud-run-runtime` (the SA created in Subtask 1.7)

### Dockerfile pattern (multi-stage, non-root)

```dockerfile
# Build stage
FROM python:3.12-slim AS build
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev
COPY app ./app

# Runtime stage
FROM python:3.12-slim AS runtime
RUN useradd --uid 10001 --no-create-home --shell /bin/false appuser
WORKDIR /app
COPY --from=build /build/.venv /app/.venv
COPY --from=build /build/app /app/app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/v1/health').read()" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### `/health` and `/readiness` semantics

- **`/health`:** liveness probe. Returns 200 unless the process is wedged. Cloud Run uses this for the container healthcheck; it does **not** check downstream dependencies. JSON: `{ "status": "ok", "version": "<commit-sha>" }`.
- **`/readiness`:** readiness probe. In Story 1.1 it returns the same payload as `/health`. Story 1.2 adds Alembic version check; Story 1.6+ may add LLM-provider warmup status. The endpoint exists now so subsequent stories evolve it without touching the load-balancer config.

Use the `commit-sha` from the env var `GIT_COMMIT_SHA` (set by CI at container build time) — fall back to `"unknown"` if unset.

### Patterns to enforce now (from Architecture § Implementation Patterns & Consistency Rules)

- **Module/file naming:** `snake_case` Python; `PascalCase.tsx` for React components; `kebab-case.ts` for hooks/utilities.
- **JSON field naming:** `snake_case`. Even on operational endpoints, keep this consistent.
- **No raw color, spacing, or font-size values in component code** — Tailwind config will hold tokens (Story 1.3 nails this down; Story 1.1 only ships the default scaffold so no tokens needed yet).
- **Structured error envelope:** `{ code, message, request_id, retry_after?, details? }` for all error responses. The middleware in Subtask 5.3 already populates `request_id`.
- **No `console.log` / `print` in production code paths** — even in this scaffold, use the structured logger in `app/observability/logging.py`.

### Testing standards (foundation only — comprehensive testing per story scope)

- **Backend:** at least one smoke test in `tests/unit/test_health.py` using `httpx.AsyncClient` against the FastAPI app, asserting `/health` returns 200 + the expected JSON shape.
- **Frontend:** at least one unit test verifying the landing page renders and the imported shadcn Button mounts (vitest + RTL).
- **CI:** both unit tests run on every PR.

### Pre-commit hooks (Subtask 3.3 dev deps include `pre-commit`)

Configure `.pre-commit-config.yaml` to run `ruff check --fix`, `ruff format`, and `mypy --strict` on staged Python files; `eslint --fix` and `prettier --write` on staged frontend files; a secret-scan hook (`detect-secrets` or `gitleaks`) on all staged files.

### Coordination notes (cross-team)

- **GCP project ownership.** Confirm with the platform team that the GCP project for the assistant is created, billing is enabled, and you have `roles/owner` (or equivalent) on it before running Terraform. If the project is shared with the existing platform, confirm naming conventions for SAs and Artifact Registry repos so we don't collide.
- **Existing-platform GitHub org / branch protection.** Confirm where the assistant's repos live (probably a new repo or two new repos in the existing org). Branch-protection rules need org-admin to set up.
- **Vercel team account.** Confirm the Vercel team / project; the GitHub integration needs to be authorized at the org level.

### Project Structure Notes

The project layouts in this story are **literally the layouts committed in Architecture § Starter Template Evaluation**. Any deviation (renaming directories, moving observability outside `app/`, etc.) is a CI failure waiting to happen — every subsequent story story uses these exact paths in its task lists. Verify alignment before completing this story.

**Detected variances (none expected):** if you find that `pnpm create next-app` defaults differ from what the Architecture spec'd (e.g., the `--src-dir` flag now produces a slightly different layout), document the variance in this story's "Completion Notes" with rationale, and update Architecture § Project Structure if the variance should propagate to other stories.

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md` § Starter Template Evaluation — Selected Starters]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Core Architectural Decisions — Infrastructure & Deployment]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Project Structure & Boundaries — Backend / Frontend project layouts]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Implementation Patterns & Consistency Rules — Naming, Structure, Process patterns]
- [Source: `_bmad-output/planning-artifacts/architecture.md` § Architecture Validation Results — Failure-Mode Matrix]
- [Source: `_bmad-output/planning-artifacts/prd.md` § Project-Type Specific Requirements — Backend Endpoint surface (`/v1/chat/turn` referenced for context; not implemented here)]
- [Source: `_bmad-output/planning-artifacts/epics.md` § Epic 1 / Story 1.1 — Acceptance Criteria source]

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context) — Claude Code dev agent. Started 2026-05-07. Local-first scaffolding scope agreed with user (no `terraform apply`, no Cloud Run / Vercel deploy, no live CI/cloud integration). Added scope per user: docker-compose for local orchestration, local Postgres container, Alembic init scaffolding (without migrations — those land in Story 1.2). Tests limited to smoke per Dev Notes.

### Debug Log References

- Initial backend `uv sync` failed: `google-adk==1.5.0` required `uvicorn>=0.34.0` while pyproject pinned `>=0.32,<0.33`. Resolution: bumped uvicorn pin to `>=0.34,<0.35`. ADK pin held.
- `pnpm build` failed first pass: shadcn semantic classes (`bg-background`, `text-foreground`, etc.) referenced before `tailwind.config.ts` mapped CSS variables to theme colors. Resolution: added `theme.extend.colors` mapping `hsl(var(--*))` per shadcn convention; added missing `--accent` / `--accent-foreground` CSS variables. Build clean.
- mypy strict flagged `CloudTraceSpanExporter()` as untyped call (third-party stub gap). Resolution: `# type: ignore[no-untyped-call]` on the single call site.
- Initial docker-compose had backend and Firestore emulator both mapped to host port 8080. Resolution: backend host port now 8000 (container stays 8080); frontend `NEXT_PUBLIC_API_BASE_URL` updated.
- ruff auto-fixed import sort + `datetime.UTC` modernization across `migrations/env.py`, `tests/conftest.py`, `app/observability/logging.py`. No semantic changes.

### Completion Notes List

**Scope agreed with user (2026-05-07): local-first this pass.** No `terraform apply`, no Cloud Run / Vercel / GitHub branch-protection changes, no live cloud verification. Cloud-deferred subtasks are flagged inline above.

**ACs delivered locally; AC1/AC3/AC4 await cloud follow-up:**

- **AC1 — GCP foundation provisioned:** Terraform code is complete and modular (network, secrets, artifact-registry, iam, github WIF). Apply + `gcloud` verification deferred. Coordination checklist in `infra/README.md` and `docs/deploy.md`.
- **AC2 — FE+BE scaffolds build and deploy:** Local build/lint/typecheck/test all green for both projects. Vercel preview + Cloud Run deploy deferred. `/v1/health` and `/v1/readiness` return the agreed JSON shape (smoke-tested via httpx ASGI).
- **AC3 — CI gates merges:** `backend-ci.yml` + `frontend-ci.yml` authored with Trivy scan. WIF apply, branch-protection, and sample-PR verification deferred.
- **AC4 — Observability emits traces and logs:** Tracing + structured logging + request-id middleware all wired. Locally `OTEL_TRACES_EXPORTER=console` prints spans to stdout; flipping to `gcp_trace` + `GOOGLE_CLOUD_PROJECT` activates Cloud Trace export. End-to-end Cloud verification deferred.

**Library version pins (2026-05-07):**

- Python `==3.12.*` (resolved by uv to 3.12.8 locally)
- `google-adk==1.5.0` (verified 2026-05-07; pinned `==` per Architecture risk mitigation)
- `anthropic==0.40.0` (pinned `==`)
- `fastapi[standard] ~0.115`, `uvicorn[standard] ~0.34` (forced by ADK transitive constraint)
- Frontend: Next 15.1.4, React 19.0.0, Tailwind 3.4.x, shadcn slate base, pnpm 9.11.0
- Terraform: `>= 1.9`, google provider `~> 6.0`

**User-requested scope additions (beyond the original story):**

- `docker-compose.yml` for full local stack (postgres + pgvector, redis, firebase emulator, backend, frontend) with healthchecks.
- Local Postgres with `pgvector/pgvector:pg16` image (Cloud SQL provisioning still belongs to Story 1.2).
- Alembic init scaffolding (`alembic.ini`, async `env.py`, `script.py.mako`); `migrations/versions/` is intentionally empty — Story 1.2 fills it.
- Firebase emulator (auth + firestore + UI). Permissive local rules; production rules ship with Story 2.2.

**Documented variances from the literal spec:**

1. **Subdir vs sibling repos:** original Dev Notes wording ("sibling repo") interpreted as monorepo subdirectories (`skate-assistant-frontend/` and `skate-assistant-backend/` under this repo) per user direction. Architecture allows this ("co-located in the repository root or its own monorepo location, your choice"). Update Architecture § Project Structure if the team prefers polyrepo.
2. **shadcn primitive set partial + filename casing carve-out (Subtask 2.3):** only `Button` is in `src/components/ui/`; pipeline is verified end-to-end. Run `pnpm dlx shadcn@latest add input dialog sheet …` (full list in original task) when downstream stories pull these in. No story is blocked. Filename `button.tsx` is lowercase per shadcn-cli convention — Architecture § Implementation Patterns now carries an explicit carve-out: *"shadcn primitives in `components/ui/` use lowercase per shadcn-cli; all other React components are `PascalCase.tsx`."*
3. **uvicorn lower bound:** bumped from `>=0.32` to `>=0.34` due to ADK 1.5.0's transitive constraint.
4. **`output: "standalone"` not enabled — deferred to Story 1.18 (pre-launch hardening):** Vercel handles output natively; left default for now. The Dockerfile's runtime image carries full `node_modules` (~300MB extra). Story 1.18 will switch to `output: "standalone"` and copy only `.next/standalone` + `.next/static`. Today's container is local-dev only; size doesn't matter.

**Cross-team coordination still required (from Dev Notes):**

- [ ] GCP project + billing for staging (and separate prod project) — confirm with platform team.
- [ ] SA + Artifact Registry naming conventions to avoid collisions on shared platform.
- [ ] GitHub org / branch-protection ownership.
- [ ] Vercel team membership + GitHub-Vercel integration scope.

**Validation results (2026-05-07):**

- Backend: `ruff check` ✅, `ruff format --check` ✅, `mypy app/` strict ✅ (14 source files), `pytest` ✅ (4/4: `/v1/health` shape, `/v1/readiness` shape, `X-Request-Id` set, `X-Request-Id` propagated when provided).
- Frontend: `pnpm lint` ✅, `pnpm typecheck` strict ✅, `pnpm test:unit` ✅ (2/2: hero heading renders, shadcn Button mounts), `pnpm build` ✅.
- `docker compose config` parses clean.

### File List

**Backend (`skate-assistant-backend/`)**

- `pyproject.toml` (new) — runtime + dev deps, ruff/mypy/pytest config, ADK pin documented
- `uv.lock` (new) — generated by `uv sync`
- `README.md` (new) — local-dev quickstart + project layout
- `.env.example` (new) — env-driven config template
- `.gitignore` (new)
- `.dockerignore` (new)
- `Dockerfile` (new) — multi-stage, non-root UID 10001, healthcheck on `/v1/health`
- `alembic.ini` (new) — async migration scaffold
- `migrations/env.py` (new) — `target_metadata=None` until Story 1.2
- `migrations/script.py.mako` (new)
- `migrations/versions/.gitkeep` (new)
- `app/__init__.py` (new)
- `app/main.py` (new) — `create_app()` + `RequestContextMiddleware` + lifespan
- `app/config.py` (new) — Pydantic Settings
- `app/dependencies.py` (new) — placeholder
- `app/api/__init__.py` (new)
- `app/api/v1/__init__.py` (new) — `/v1` router aggregation
- `app/api/v1/ops.py` (new) — `/health`, `/readiness`
- `app/api/exceptions.py` (new, post-review) — structured-error-envelope handlers (HTTPException / RequestValidationError / Exception)
- `app/agents/__init__.py` (new) — placeholder package
- `app/compatibility/__init__.py` (new) — placeholder
- `app/models/__init__.py` (new) — placeholder
- `app/services/__init__.py` (new) — placeholder
- `app/observability/__init__.py` (new) — re-exports
- `app/observability/logging.py` (new) — JSON formatter + contextvars
- `app/observability/tracing.py` (new) — OTel + Cloud Trace exporter
- `tests/__init__.py` (new)
- `tests/conftest.py` (new) — httpx ASGI client fixture
- `tests/unit/__init__.py` (new)
- `tests/unit/test_health.py` (new) — 4 smoke tests
- `tests/unit/test_exceptions.py` (new, post-review) — 2 envelope-shape smoke tests (HTTP exception + unhandled exception)
- `tests/integration/__init__.py` (new)
- `tests/eval/.gitkeep` (new)

**Frontend (`skate-assistant-frontend/`)**

- `package.json` (new) — Next 15.1.4 + React 19 + Firebase + shadcn deps + test deps
- `pnpm-lock.yaml` (new) — generated by `pnpm install`
- `tsconfig.json` (new) — strict mode, `@/*` import alias
- `next.config.ts` (new)
- `tailwind.config.ts` (new) — slate base + theme tokens mapped to CSS vars
- `postcss.config.mjs` (new)
- `components.json` (new) — shadcn config
- `eslint.config.mjs` (new) — Next + TS rules via FlatCompat
- `vitest.config.ts` (new) — jsdom env, `@/*` alias, `tests/setup.ts`
- `Dockerfile` (new) — multi-stage Node 22-alpine, non-root UID 10001
- `.gitignore` (new)
- `.dockerignore` (new)
- `.env.example` (new)
- `README.md` (new)
- `src/app/layout.tsx` (new)
- `src/app/page.tsx` (new) — landing page importing shadcn Button
- `src/app/globals.css` (new) — Tailwind layers + slate CSS variables
- `src/components/ui/button.tsx` (new) — shadcn Button (only primitive shipped this story)
- `src/lib/utils.ts` (new) — `cn()` helper
- `src/lib/.gitkeep` (new)
- `tests/setup.ts` (new) — jest-dom setup
- `tests/landing-page.test.tsx` (new) — 2 vitest smoke tests

**Infra (`infra/`)**

- `README.md` (new) — apply order + cross-team checklist
- `terraform/.gitignore` (new)
- `terraform/backend.tf` (new) — GCS state config
- `terraform/main.tf` (new) — provider + module composition
- `terraform/variables.tf` (new) — `project_id`, `region`, `environment`
- `terraform/terraform.tfvars.example` (new)
- `terraform/modules/network/main.tf` (new) — VPC + subnet + VPC connector
- `terraform/modules/secrets/main.tf` (new) — Secret Manager + 4 placeholders
- `terraform/modules/artifact-registry/main.tf` (new) — Docker repo + cleanup policies
- `terraform/modules/iam/main.tf` (new) — 3 SAs + role bindings (least-privilege per matrix)
- `github/workload-identity.tf` (new) — OIDC pool + provider + ci SA federation
- `github/terraform.tfvars.example` (new, post-review) — sample vars for the WIF apply

**CI (`/.github/workflows/`)**

- `backend-ci.yml` (new) — lint + typecheck + test + container build + Trivy (no `ignore-unfixed`) + SARIF upload to code scanning; deploy commented
- `frontend-ci.yml` (new) — lint + typecheck + test + build
- `infra-ci.yml` (new, post-review) — `terraform fmt -check`, `terraform validate`, `tflint` for `infra/**`

**Repo root**

- `docker-compose.yml` (new) — full local stack with healthcheck-gated dependencies
- `firebase.json` (new) — production-target Firestore config (strict-deny rules)
- `firebase.local.json` (new, post-review) — emulator-only config (permissive rules)
- `.firebaserc` (new) — local project ID
- `firestore.rules` (new) — strict-deny default; safe for any `firebase deploy`
- `firestore.rules.local` (new, post-review) — permissive rules used only by the local emulator
- `.pre-commit-config.yaml` (new) — ruff + mypy + prettier + gitleaks
- `.gitignore` (modified) — added Terraform / mypy-cache / ruff-cache / Playwright / firestore-debug entries
- `docs/deploy.md` (new) — local-first quickstart + deferred cloud apply order

**BMad artifacts (modified)**

- `_bmad-output/implementation-artifacts/sprint-status.yaml` — 1-1 status: ready-for-dev → in-progress
- `_bmad-output/implementation-artifacts/1-1-project-foundation-and-gcp-infrastructure.md` — Status, Tasks/Subtasks, Dev Agent Record, File List, Change Log

### Review Follow-ups (AI)

> Generated by code review on 2026-05-07. Three parallel reviewers: Blind Hunter (diff only), Edge Case Hunter (diff + project), Acceptance Auditor (diff + spec). 41 actionable items after dedupe.

**Decision needed — all resolved 2026-05-07:**

- [x] [Review][Patch] **D1 → Lazy `get_settings()` with `@lru_cache`** [`skate-assistant-backend/app/config.py`] — Replace global `settings = Settings()` with `@lru_cache def get_settings() -> Settings`. Update all callers (`config.py`, `main.py`, `observability/{logging,tracing}.py`, `migrations/env.py`, `api/v1/ops.py`) to call `get_settings()`. Fixes import-time crash + improves test isolation.
- [x] [Review][Patch] **D2 → Document shadcn carve-out** [Architecture § Implementation Patterns + Story 1.1 Completion Notes variance #2] — Add wording: *"shadcn-generated primitives in `components/ui/` use lowercase filenames per shadcn-cli convention; all other React components are `PascalCase.tsx`."* No file moves.
- [x] [Review][Patch] **D3 → Land structured-error-envelope exception handlers now** [new `skate-assistant-backend/app/api/exceptions.py` + wired in `app/main.py`] — Register handlers for `HTTPException`, `RequestValidationError`, and unhandled `Exception` returning `{code, message, request_id, retry_after?, details?}`. `request_id` pulled from `request.state.request_id` (already populated). Couples with M1 (header on error path).
- [x] [Review][Patch] **D4 → Add `.github/workflows/infra-ci.yml`** — `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`, `tflint`. Triggered on `infra/**` and the workflow itself. No cloud creds required.
- [x] [Review][Patch] **D5 → Drop `ignore-unfixed` + upload SARIF** [`.github/workflows/backend-ci.yml:120-125`] — Remove `ignore-unfixed: true`. Add second Trivy step with `format: sarif` and `github/codeql-action/upload-sarif@v3` so unfixed CVEs surface in GitHub code scanning. Build fails on CRITICAL/HIGH regardless of upstream fix status.
- [x] [Review][Defer] **D6 → Frontend image size optimization** [`skate-assistant-frontend/Dockerfile`, `next.config.ts`] — deferred to Story 1.18 (pre-launch hardening). Update Completion Notes variance #5 to reference Story 1.18 explicitly. Today's container is local-dev only; size doesn't matter.

**Patch (apply before merge):**

- [x] [Review][Patch] **H1 — Request-id NOT propagated as a span attribute** [`skate-assistant-backend/app/main.py` middleware] — Subtask 5.3 explicit requirement contradicting AC4. Add `trace.get_current_span().set_attribute("request_id", request_id)` inside `RequestContextMiddleware.dispatch` after determining `request_id`. Required for log↔trace correlation.
- [x] [Review][Patch] **H2 — Permissive Firestore rules deploy footgun** [`firestore.rules`, `firebase.json:9`] — `firebase deploy --only firestore:rules` (with `--project` override) would publish open rules globally. Rename current rules to `firestore.rules.local`, point `firebase.json` at it only when running emulator, and create a strict-deny `firestore.rules` for any deploy path.
- [x] [Review][Patch] **M1 — Error path drops `X-Request-Id` response header** [`skate-assistant-backend/app/main.py:53-65`] — `BaseHTTPMiddleware.dispatch` re-raises before adding header, so 500s lack the correlation ID AC4 promises. Register a FastAPI `exception_handler` that sets `X-Request-Id` from `request.state.request_id` on the error response (couples with D3).
- [x] [Review][Patch] **M2 — Alembic env.py URL invisible to async engine** [`skate-assistant-backend/migrations/env.py`] — `config.set_main_option("sqlalchemy.url", ...)` writes to main options, but `async_engine_from_config(config.get_section(...))` reads from the `[alembic]` section dict — the URL isn't there. Fix: build the engine directly via `create_async_engine(settings.database_url, poolclass=NullPool)`.
- [x] [Review][Patch] **M4 — `--frozen` fallback defeats reproducibility** [`skate-assistant-backend/Dockerfile:14-16`, `skate-assistant-frontend/Dockerfile:7`, `.github/workflows/backend-ci.yml:84`] — Drop the `|| <unfrozen>` clauses everywhere. If the lockfile is stale, fail loudly; do not silently regenerate inside the build.
- [x] [Review][Patch] **M7 — Cloud Trace exporter silent fall-through to ADC** [`skate-assistant-backend/app/observability/tracing.py:21-26`] — When `OTEL_TRACES_EXPORTER=gcp_trace` and `GOOGLE_CLOUD_PROJECT=""`, exporter falls back to `google.auth.default()` discovery (may pick wrong project, may raise async). Require non-empty `google_cloud_project` via `model_validator` when exporter is `gcp_trace`; emit a startup log line stating the resolved project.
- [x] [Review][Patch] **M8 — `provider.shutdown()` not called on lifespan exit** [`skate-assistant-backend/app/main.py:69-76`, `app/observability/tracing.py`] — `BatchSpanProcessor` buffers in memory; SIGTERM drops in-flight spans. Capture the provider in `init_tracing` (or expose via `app.state`) and call `provider.shutdown()` in the lifespan `finally` block.
- [x] [Review][Patch] **M9 — uvicorn has no `--timeout-graceful-shutdown`** [`skate-assistant-backend/Dockerfile:41`] — Cloud Run sends SIGTERM with a default 10s wait; long requests (60min SSE in Story 1.5) will SIGKILL. Add `--timeout-graceful-shutdown=30` to the CMD.
- [x] [Review][Patch] **M10 — CI path filters miss root configs** [`.github/workflows/{backend-ci,frontend-ci}.yml`] — Edits to `docker-compose.yml`, `firebase.json`, `firestore.rules`, `.firebaserc` don't trigger any workflow. Add the relevant root files to `paths:` for both workflows (or split into a `repo-wide-ci.yml`).
- [x] [Review][Patch] **M12 — `Button` uses `forwardRef` without `"use client"`** [`skate-assistant-frontend/src/components/ui/button.tsx:1`] — Will break with `Event handlers cannot be passed to Client Component props` as soon as Story 1.4 attaches `onClick`. Add `"use client";` directive at top of file. (shadcn-cli output normally includes this — appears to have been stripped during my hand-authoring.)
- [x] [Review][Patch] **M13 — Cloud Trace exporter init failure crashes lifespan** [`skate-assistant-backend/app/observability/tracing.py:21-26`] — Only `ImportError` is caught; `DefaultCredentialsError` propagates and brings the app down. Wrap the exporter construction in a broader `try/except` that logs the failure and falls back to `ConsoleSpanExporter`.
- [x] [Review][Patch] **L1 — `Read(//tmp/**)` double-slash typo** [`.claude/settings.local.json:24`] — Path-glob never matches with leading `//`. Fix to `Read(/tmp/**)`.
- [x] [Review][Patch] **L2 — Healthcheck `urllib.urlopen` no timeout** [`skate-assistant-backend/Dockerfile:43`] — Add `timeout=3` kwarg so a hung backend returns a clean failure code.
- [x] [Review][Patch] **L3 — `firebase-tools:latest` not pinned** [`docker-compose.yml:33`] — Pin to a specific version + digest. Prefer an official image source over `andreysenov/...`.
- [x] [Review][Patch] **L5 — No `concurrency:` group in CI workflows** [`.github/workflows/{backend-ci,frontend-ci}.yml`] — Add `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` to both. Saves CI minutes, prevents `type=gha` cache races.
- [x] [Review][Patch] **L6 — Tests share global tracer state across `create_app()` calls** [`skate-assistant-backend/app/observability/tracing.py:50`, `tests/conftest.py:13-14`] — `trace.set_tracer_provider` is global; per-test `create_app()` triggers a "Overriding of current TracerProvider is not allowed" warning. Guard `init_tracing` with a module-level flag (idempotent) or accept a TracerProvider arg for tests.
- [x] [Review][Patch] **L7 — Gratuitous `__init__` override + untyped `dispatch`** [`skate-assistant-backend/app/main.py:30-38`] — Remove the `__init__` override; type `call_next: RequestResponseEndpoint` from `starlette.middleware.base` and drop the `# type: ignore`.
- [x] [Review][Patch] **L8 — `_build_exporter` dead `return None` branch** [`skate-assistant-backend/app/observability/tracing.py:32`] — `Literal[...]` already exhausts the cases; mypy strict will eventually flag this. Remove or use `assert_never`.
- [x] [Review][Patch] **L9 — `extra="ignore"` swallows `.env` typos** [`skate-assistant-backend/app/config.py:16`] — Switch to `extra="forbid"` so `LOG_LEVELl=DEBUG` fails fast.
- [x] [Review][Patch] **L10 — `DATABASE_URL` accepts any string, no `+asyncpg` check** [`skate-assistant-backend/app/config.py:25`] — Add a `@field_validator("database_url")` asserting `+asyncpg` driver prefix. Saves a confusing Alembic-time crash.
- [x] [Review][Patch] **L12 — VPC connector CIDR hardcoded `10.20.0.0/28`** [`infra/terraform/modules/network/main.tf:32`] — Parameterize via a module variable (`connector_cidr`) defaulting to current value, so platform team can override without forking the module.
- [x] [Review][Patch] **L13 — Firebase emulator `service_started` race** [`docker-compose.yml:67-68`] — Add a healthcheck on `firebase-emulator` (e.g. `curl -fsS http://localhost:9099 || exit 1` after a `start_period`), then switch backend's depends_on to `service_healthy`.
- [x] [Review][Patch] **L14 — Frontend depends_on backend without healthcheck** [`docker-compose.yml:84-86`] — Add a healthcheck to backend service (compose-level — Dockerfile's HEALTHCHECK isn't surfaced to compose) and gate frontend on `service_healthy`.
- [x] [Review][Patch] **L15 — uv version skew (local 0.11.7 vs CI/Docker 0.5.11)** [`Dockerfile`, `.github/workflows/backend-ci.yml`] — Reconcile to one pin. Either bump CI/Docker to 0.11.7 or document why local is allowed to drift ahead.
- [x] [Review][Patch] **L16 — `request_id_ctx.reset(token)` may dereference unbound** [`skate-assistant-backend/app/main.py:38-65`] — Initialize `token_id, token_path, token_status, token_duration = None` before the `try` block; check `is not None` in `finally` before calling `.reset(...)`.
- [x] [Review][Patch] **L17 — Artifact Registry `keep-last-10` shadows `delete-untagged-after-7d`** [`infra/terraform/modules/artifact-registry/main.tf:18-32`] — KEEP rules win over DELETE; an UNTAGGED image among the most-recent-10 is kept indefinitely. Add `condition { tag_state = "TAGGED" }` to the keep policy.
- [x] [Review][Patch] **L18 — `terraform.tfvars.example` has no GitHub-WIF sample** [`infra/terraform/terraform.tfvars.example` and `infra/github/`] — Add `github.tfvars.example` (or extend the existing example) with `github_repository`, `ci_service_account_email` placeholders.
- [x] [Review][Patch] **L19 — `mypy` not run on `tests/`** [`.github/workflows/backend-ci.yml:38`] — Extend to `uv run mypy app/ tests/` (or relax test-only mypy rules in `pyproject.toml`).
- [x] [Review][Patch] **L20 — Inbound `X-Request-Id` length/charset unbounded** [`skate-assistant-backend/app/main.py:35-36`] — Cap to 128 chars + regex `^[A-Za-z0-9._-]+$` before honoring; otherwise generate fresh UUID. Prevents log pollution and CRLF-injection-shaped payloads.
- [x] [Review][Patch] **L21 — Over-cautious "healthcheck variance" in Completion Notes** [story file, Completion Notes variance #3] — Dev Notes literal Dockerfile snippet already shows `/v1/health`; the variance note is redundant. Remove it to keep the variance list focused on real deviations.

**Defer (cloud follow-up or forward-looking):**

- [x] [Review][Defer] **DE1 — WIF `attribute_condition` lacks `attribute.ref` constraint** [`infra/github/workload-identity.tf:55`] — deferred to Story 1.1-cloud (apply-time concern; need to scope to refs/heads/main + per-env split before any cloud deploy)
- [x] [Review][Defer] **DE2 — `NEXT_PUBLIC_API_BASE_URL` won't work for SSR fetches inside docker** [`docker-compose.yml:89`] — deferred to Story 1.4 (no SSR fetches today; will need split into `INTERNAL_API_BASE_URL=http://backend:8080`)
- [x] [Review][Defer] **DE3 — `git_commit_sha` defaults to "unknown"** [`skate-assistant-backend/app/config.py:22`] — deferred (CI sets `GIT_COMMIT_SHA` at build; only affects local dev where it's intentional)
- [x] [Review][Defer] **DE4 — Empty-string defaults for required-in-prod secret refs** [`skate-assistant-backend/app/config.py:33-37`] — deferred to Story 1.4+ (loaders will validate at first use)
- [x] [Review][Defer] **DE5 — `migration-job` SA has zero role bindings** [`infra/terraform/modules/iam/main.tf:49-54`] — deferred to Story 1.2 (matrix-correct; cloudsql.client lands with Cloud SQL provisioning)
- [x] [Review][Defer] **DE6 — VPC connector min/max instances at floor (200/300 Mbps)** [`infra/terraform/modules/network/main.tf:33-34`] — deferred to Story 1.18 (production tuning)
- [x] [Review][Defer] **DE7 — Secret Manager `replication: auto`** [`infra/terraform/modules/secrets/main.tf:26`] — deferred (data-residency decision pending; comment in module documents the cadence-per-secret intake required first)

## Senior Developer Review (AI)

**Reviewed:** 2026-05-07
**Reviewer model:** claude-opus-4-7 (1M context) — three parallel layers:
- Blind Hunter (diff only, 19 findings)
- Edge Case Hunter (diff + project, 50 findings across 9 lenses)
- Acceptance Auditor (diff + spec, 17 findings + verdict matrix)

**Outcome (initial):** **Changes Requested** — 2 HIGH and 9 MEDIUM patch items + 6 decision-needed.

**Outcome (after patch round, 2026-05-07):** **Approved** — all 33 patches applied; 6 decision-needed resolved (5 patched, 1 deferred to Story 1.18). All validations green.

**Severity breakdown (post-dedupe + triage):**

| Severity | Patch | Decision-needed | Defer | Total |
|---|---|---|---|---|
| HIGH | 2 | 0 | 0 | 2 |
| MEDIUM | 9 | 4 | 0 | 13 |
| LOW | 17 | 2 | 7 | 26 |
| **Total** | **28** | **6** | **7** | **41** |

Plus ~12 dismissed (forward-looking, already-acknowledged, or noise).

**Verdict by AC** (per Acceptance Auditor):

| AC | Verdict | Notes |
|---|---|---|
| AC1 | Local-only OK (cloud apply deferred) | Terraform code matches IAM matrix exactly; rotation deferred per intake (acknowledged). |
| AC2 | **PARTIAL — in-scope defects** | Builds + tests green. Open: (a) `button.tsx` lowercase vs PascalCase rule (D2), (b) shadcn primitive set is just Button (acknowledged `(partial)`), (c) `Button` missing `"use client"` (M12). |
| AC3 | Local-only OK (cloud integration deferred) | Workflows authored; Trivy block matches. Path filter gaps (M10) and infra-ci gap (D4) are in-scope CI defects. |
| AC4 | **PARTIAL — in-scope defect** | Logging + middleware deliver. **request_id NOT added as span attribute** (H1) — Subtask 5.3 explicit; log↔trace correlation impossible without out-of-band step. |

**Concentrated risk areas:** observability/middleware lifecycle (5 findings cluster: H1, M1, M7, M8, M13), Dockerfile/CI reproducibility (3 findings: M4, L11, L15), docker-compose port/DNS coordination (3 findings: L13, L14, plus DE2 forward).

**Files most affected:** `skate-assistant-backend/app/main.py` (5 findings), `skate-assistant-backend/app/observability/tracing.py` (4), `skate-assistant-backend/Dockerfile` (3), `docker-compose.yml` (3), `.github/workflows/backend-ci.yml` (4).

## Change Log

| Date       | Change                                                                                                  |
|------------|---------------------------------------------------------------------------------------------------------|
| 2026-05-07 | Story scaffolded under local-first scope (user-confirmed). Backend + frontend + infra + CI all coded.   |
| 2026-05-07 | All cloud-side subtasks (1.2, 1.8, 4.4 apply, 4.5, 4.6, 5.4, 6.1–6.6) deferred pending platform-team coordination + credentials. |
| 2026-05-07 | Added local-orchestration scope (Task 7) per user request: docker-compose, postgres+pgvector, redis, firebase emulator, alembic init scaffold, pre-commit hooks. |
| 2026-05-07 | Status promoted to `review` — local-first scope treated as the deliverable boundary. Deferred cloud subtasks tracked for a follow-up "1.1-cloud" story when GCP/Vercel/GitHub access lands. |
| 2026-05-07 | Code review (3-layer: Blind Hunter / Edge Case Hunter / Acceptance Auditor) surfaced 41 actionable findings. Triage: 33 patches + 6 decision-needed + 7 deferred + ~12 dismissed. |
| 2026-05-07 | Patch round applied: H1 span-attribute, H2 firestore split (rules/local + strict-deny default + firebase.local.json), 11 medium-sev fixes (middleware error path, Alembic engine, frozen-fallback drops, exporter resilience, lifespan provider.shutdown, uvicorn graceful timeout, CI path filters, `Button "use client"`, exception envelope handlers, settings lazy-load + validators), 17 low-sev fixes. Added new files: `app/api/exceptions.py`, `tests/unit/test_exceptions.py`, `.github/workflows/infra-ci.yml`, `firebase.local.json`, `firestore.rules.local`, `infra/github/terraform.tfvars.example`. Status promoted `review → done`. |
