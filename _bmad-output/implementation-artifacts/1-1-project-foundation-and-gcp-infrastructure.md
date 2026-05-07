# Story 1.1: Project Foundation & GCP Infrastructure

Status: ready-for-dev

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

- [ ] **Task 1: Initialize Terraform IaC repository** (AC: 1)
  - [ ] Subtask 1.1: Create `infra/` directory at the project root with `terraform/` subdirectory; commit a `.gitignore` excluding `.terraform/`, `*.tfstate*`, `*.tfvars` (except example).
  - [ ] Subtask 1.2: Create a GCS bucket `<project-id>-terraform-state` with **object versioning enabled**; configure as Terraform state backend in `terraform/backend.tf`.
  - [ ] Subtask 1.3: Define GCP provider in `terraform/main.tf` with project, region (`us-central1` default — confirm in `terraform.tfvars.example`), and credentials via Application Default Credentials.
  - [ ] Subtask 1.4: Create Terraform module `terraform/modules/network/` provisioning a VPC + private subnet (`/24`) for Cloud Run + Cloud SQL connectivity. Include VPC connector for Cloud Run egress.
  - [ ] Subtask 1.5: Create Terraform module `terraform/modules/secrets/` enabling Secret Manager API; pre-create empty placeholder secrets: `firebase-admin-credentials`, `anthropic-api-key`, `langfuse-api-key`, `anonymous-jwt-signing-secret` (rotation policies set per intake).
  - [ ] Subtask 1.6: Create Terraform module `terraform/modules/artifact-registry/` provisioning an Artifact Registry **Docker repository** named `skate-assistant-backend` in the chosen region.
  - [ ] Subtask 1.7: Create Terraform module `terraform/modules/iam/` provisioning three service accounts: `cloud-run-runtime`, `ci`, `migration-job`; bind only the minimum roles each needs (see *IAM Role Matrix* in Dev Notes).
  - [ ] Subtask 1.8: Run `terraform plan` against staging; review output; run `terraform apply`; verify all resources via `gcloud` CLI.

- [ ] **Task 2: Scaffold frontend project** (AC: 2)
  - [ ] Subtask 2.1: Run `pnpm create next-app@latest skate-assistant-frontend --typescript --tailwind --app --src-dir --import-alias "@/*"` and commit the result as the initial frontend repo state.
  - [ ] Subtask 2.2: Initialize shadcn/ui with `pnpm dlx shadcn@latest init -d` accepting defaults (slate base, neutral palette).
  - [ ] Subtask 2.3: Install starter component set: `pnpm dlx shadcn@latest add button input dialog sheet toast tabs tooltip popover accordion skeleton scroll-area avatar badge card switch select separator dropdown-menu`. Components land in `src/components/ui/` — these are owned in-repo (no library import). **Do NOT** customize tokens yet (that is Story 1.3).
  - [ ] Subtask 2.4: Add Firebase client SDK: `pnpm add firebase`. Add testing: `pnpm add -D @axe-core/playwright @playwright/test vitest @testing-library/react @testing-library/jest-dom`.
  - [ ] Subtask 2.5: Add `next.config.ts` configuration: enable Turbopack for dev, set `output: 'standalone'` (only if needed for self-hosting; Vercel default is fine), configure `images.remotePatterns` for catalog product images (placeholder for now).
  - [ ] Subtask 2.6: Replace `src/app/page.tsx` with a minimal landing page that imports a shadcn Button to verify the component pipeline; no real UX yet.
  - [ ] Subtask 2.7: Verify `pnpm build` and `pnpm lint` succeed with zero errors; commit.

- [ ] **Task 3: Scaffold backend project** (AC: 2)
  - [ ] Subtask 3.1: Initialize Python 3.12 project with `uv init --python 3.12` in a sibling repo `skate-assistant-backend/`.
  - [ ] Subtask 3.2: Add core runtime deps via `uv add`: `"fastapi[standard]"`, `google-adk`, `pydantic-settings`, `"sqlalchemy[asyncio]"`, `asyncpg`, `alembic`, `firebase-admin`, `google-cloud-firestore`, `google-cloud-secret-manager`, `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-exporter-gcp-trace`, `pgvector`, `redis`, `httpx`. **Pin ADK version** explicitly per Architecture risk mitigation; document in `pyproject.toml` comments.
  - [ ] Subtask 3.3: Add dev deps: `uv add --dev pytest pytest-asyncio httpx ruff mypy pre-commit`.
  - [ ] Subtask 3.4: Create the project structure exactly as specified in *Architecture / Project Structure (backend)*: `app/{api/v1,agents,compatibility,models,services,observability}` and `tests/{unit,integration,eval}`. Empty `__init__.py` in each Python package directory; placeholder docstring at the top of each.
  - [ ] Subtask 3.5: Implement `app/main.py` with a minimal FastAPI app — app factory pattern, OpenTelemetry instrumentation init at startup, lifespan for graceful shutdown.
  - [ ] Subtask 3.6: Implement `app/config.py` with Pydantic Settings: `environment` (dev/staging/prod), `region`, `log_level`, secret-name references (NOT secret values — values come from Secret Manager at runtime).
  - [ ] Subtask 3.7: Implement `app/api/v1/ops.py` with two endpoints: `GET /health` and `GET /readiness`. Both return JSON `{ "status": "ok", "version": "<commit-sha>", "schema_version": "<alembic-rev or null>" }`. Schema version is null in this story (Cloud SQL is Story 1.2); the structure must already exist so Story 1.2 only fills it in.
  - [ ] Subtask 3.8: Wire `ops.py` router into `app/main.py` under `/v1/`.
  - [ ] Subtask 3.9: Create multi-stage `Dockerfile` (Python slim base; build stage installs deps via `uv`; runtime stage copies wheel + app, runs as non-root user `appuser` UID 10001, sets `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]`); include healthcheck instruction targeting `/health`.
  - [ ] Subtask 3.10: Create `.dockerignore` excluding `.git`, `.venv`, `tests/`, `migrations/versions/__pycache__`, `.env*`.
  - [ ] Subtask 3.11: Verify `uv run uvicorn app.main:app --reload` starts cleanly and `curl localhost:8000/v1/health` returns the expected JSON. Verify `ruff check` and `mypy app/` succeed; commit.

- [ ] **Task 4: GitHub Actions CI/CD pipeline** (AC: 3)
  - [ ] Subtask 4.1: Create `.github/workflows/backend-ci.yml` triggered on PRs touching `skate-assistant-backend/**`. Steps: checkout, install uv, `uv sync`, `ruff check`, `mypy app/`, `pytest tests/unit`, build container, push to Artifact Registry (only on `main`), deploy to Cloud Run staging (only on `main`).
  - [ ] Subtask 4.2: Create `.github/workflows/frontend-ci.yml` triggered on PRs touching `skate-assistant-frontend/**`. Steps: checkout, install pnpm, `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm typecheck` (`tsc --noEmit`), `pnpm test:unit`, `pnpm build`, deploy to Vercel preview (Vercel handles deploy via the Vercel-GitHub integration; this workflow just ensures CI gates first).
  - [ ] Subtask 4.3: Add **container vulnerability scan** step to backend workflow using Trivy: `aquasecurity/trivy-action@master` with `severity: CRITICAL,HIGH` and `exit-code: 1`.
  - [ ] Subtask 4.4: Configure GitHub OIDC for keyless GCP authentication: bind the GitHub repo to the `ci` service account via Workload Identity Federation pool. Document the binding in `infra/terraform/modules/iam/`.
  - [ ] Subtask 4.5: Configure GitHub branch protection on `main` to require backend-ci AND frontend-ci status checks before merge; require ≥ 1 review.
  - [ ] Subtask 4.6: Open a sample PR with a trivial change to verify both workflows run and gate the merge.

- [ ] **Task 5: Observability foundation** (AC: 4)
  - [ ] Subtask 5.1: Implement `app/observability/tracing.py` with an `init_tracing()` function: configure OpenTelemetry `TracerProvider`, `BatchSpanProcessor`, and `CloudTraceSpanExporter` (from `opentelemetry-exporter-gcp-trace`). Auto-instrument FastAPI via `FastAPIInstrumentor.instrument_app(app)` after app creation.
  - [ ] Subtask 5.2: Implement structured logging in `app/observability/logging.py`: configure stdlib `logging` with a JSON formatter that emits `{ timestamp, severity, message, request_id, path, status, duration_ms }` to stdout (Cloud Logging auto-ingests stdout from Cloud Run).
  - [ ] Subtask 5.3: Add a FastAPI middleware in `app/main.py` that generates a `request_id` (UUID v4) per request, populates it on `request.state`, includes it in every log line and as a span attribute. The same `request_id` is returned to clients via the `X-Request-Id` response header.
  - [ ] Subtask 5.4: Deploy the staging build, hit `/health` from a browser, and verify in the Cloud Console: trace appears in Cloud Trace within 60 seconds, structured log appears in Cloud Logging with the `request_id` field.

- [ ] **Task 6: Deploy and verify end-to-end** (AC: 1, 2, 3, 4)
  - [ ] Subtask 6.1: Run `terraform apply` against staging.
  - [ ] Subtask 6.2: Push the backend container image to Artifact Registry; deploy revision to Cloud Run staging.
  - [ ] Subtask 6.3: Push the frontend to Vercel via the Vercel GitHub integration; verify the preview URL renders.
  - [ ] Subtask 6.4: Curl `https://<staging-url>/v1/health` and `/v1/readiness`; both return 200 + expected JSON.
  - [ ] Subtask 6.5: Open a fresh sample PR; verify CI runs both workflows and would block merge on a failed lint.
  - [ ] Subtask 6.6: Verify trace IDs appear in Cloud Trace; verify log entries in Cloud Logging.
  - [ ] Subtask 6.7: Document the deployment in a brief `docs/deploy.md` (or `README.md` section) — what commands run, where state lives, where logs/traces are.

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

_To be filled in by the dev agent on first commit._

### Debug Log References

_To be filled in by the dev agent during implementation._

### Completion Notes List

_To be filled in by the dev agent on completion. Document any deviations from the spec, library version pins chosen, ADK version verified, and any cross-team coordination outcomes._

### File List

_To be filled in by the dev agent on completion. List every file created or modified by this story, organized by frontend / backend / infra._
