# Story 1.2: Cloud SQL Provisioning + Alembic Initial Schema + CI Gate

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a development team,
I want Cloud SQL provisioned with Alembic-managed schema migrations and CI gates,
so that all schema changes flow through versioned, reversible migrations from day one with zero drift.

## Acceptance Criteria

1. **Given** the GCP foundation exists  
   **When** Terraform provisions Cloud SQL Postgres 16 (HA primary + read replica)  
   **Then** the database is reachable via private IP from Cloud Run with `assistant_read_only` and `assistant_read_write` roles created  
   **And** automatic backups (35-day retention) and PITR are enabled
2. **Given** Cloud SQL exists  
   **When** `alembic upgrade head` runs the initial migration  
   **Then** baseline tables are created (`alembic_version`, `audit_log` placeholder)  
   **And** the migration is fully reversible (`downgrade -1` returns to baseline)
3. **Given** an Alembic migration is committed in a PR  
   **When** the migration CI gate runs  
   **Then** CI executes `upgrade head` -> `downgrade -1` -> `upgrade head` and any failure blocks merge
4. **Given** the FastAPI service starts  
   **When** the application boots  
   **Then** it queries `alembic_version`; if the schema version does not match the application's expected version, the service refuses to start with a clear error logged to Cloud Logging

## Tasks / Subtasks

- [x] **Task 1: Provision Cloud SQL and networking in Terraform** (AC: 1)
  - [x] Add `infra/terraform/modules/cloud-sql/` with primary + read replica resources (Postgres 16, regional HA primary).
  - [x] Configure private IP connectivity and required service networking/VPC wiring consistent with existing `network` module outputs.
  - [x] Add DB backups + PITR configuration (35-day retention target).
  - [x] Create DB roles/users for `assistant_read_only` and `assistant_read_write` with least privilege.
  - [x] Wire module into `infra/terraform/main.tf`, `infra/terraform/variables.tf`, and `infra/terraform/terraform.tfvars.example`.
  - [x] Update `infra/README.md` and `docs/deploy.md` with apply sequence and verification commands for Cloud SQL.

- [x] **Task 2: Land initial Alembic schema and async migration correctness** (AC: 2)
  - [x] Create first migration under `skate-assistant-backend/migrations/versions/` for baseline tables: `audit_log` and revision metadata.
  - [x] Ensure migration downgrade cleanly removes created objects and restores pre-migration baseline.
  - [x] Keep migration idempotent/reversible discipline aligned with architecture constraints.
  - [x] Update `skate-assistant-backend/migrations/env.py` only as needed to keep async engine behavior correct with `asyncpg`.
  - [x] Add/update SQLAlchemy model placeholders in `skate-assistant-backend/app/models/` if needed to support consistent migration ownership.

- [x] **Task 3: Add migration CI gate for upgrade/downgrade/upgrade** (AC: 3)
  - [x] Extend `.github/workflows/backend-ci.yml` to run `alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head`.
  - [x] Ensure the migration gate runs in a deterministic database target during CI (ephemeral service DB or stable CI DB container).
  - [x] Make migration failures merge-blocking (non-zero exit).
  - [x] Keep existing lint/type/test/security gates intact.

- [x] **Task 4: Enforce schema drift check on FastAPI startup** (AC: 4)
  - [x] Implement startup check in `skate-assistant-backend/app/main.py` (or a dedicated startup dependency) that compares expected Alembic head vs runtime DB `alembic_version`.
  - [x] Log a clear structured error (including requestless startup context) and fail startup on mismatch.
  - [x] Preserve existing `/v1/health` and `/v1/readiness` contract shape.
  - [x] Update readiness semantics to report actual schema version instead of `null` once migration is applied.

- [x] **Task 5: Add tests for migration discipline and startup drift behavior** (AC: 2, 3, 4)
  - [x] Add backend tests validating migration round-trip behavior and drift-check failure path.
  - [x] Keep tests under `skate-assistant-backend/tests/` aligned with existing strict mypy/ruff settings.
  - [x] Verify CI still passes with new migration checks and tests enabled.

## Dev Notes

### Epic Context (from Epic 1)

- Story 1.2 is the first persistent-data story after foundational scaffolding.
- This story unlocks downstream catalog and compatibility stories that depend on stable schema/versioning discipline (`1-7`, `1-8`, `3-2` references in epics).
- Must maintain strict "Alembic-only, reversible, CI-validated" governance from architecture and epics.

### Previous Story Intelligence (Story 1.1)

- Story 1.1 already created:
  - Alembic scaffolding (`alembic.ini`, async `migrations/env.py`, `migrations/script.py.mako`)
  - Backend strict lint/type/test baseline
  - Infra module pattern (`modules/network`, `secrets`, `artifact-registry`, `iam`) and CI conventions.
- Known 1.1 review fixes that must be preserved:
  - `migrations/env.py` async engine handling was corrected to avoid section/config pitfalls.
  - Backend CI intentionally fails loudly on reproducibility/security failures (no silent fallbacks).
  - Structured logging + request-id patterns are already enforced in backend runtime.
- Story file `1-1-project-foundation-and-gcp-infrastructure.md` is the canonical continuity source for patterns and constraints.

### Architecture Compliance Requirements

- Cloud: GCP managed services; DB is Cloud SQL PostgreSQL 16 via private IP.
- Migrations: Alembic is mandatory, async-aware, reversible, CI-gated (`upgrade head -> downgrade -1 -> upgrade head`).
- Deployment model: Cloud Run + Terraform IaC; migration step is part of release discipline (Cloud Run Job pre-step for deploy flows).
- Maintain stateless FastAPI app behavior while adding startup schema checks.

### File Structure Requirements (expected touch points)

- **Infra/Terraform**
  - `infra/terraform/main.tf` (module wiring)
  - `infra/terraform/variables.tf`
  - `infra/terraform/terraform.tfvars.example`
  - `infra/terraform/modules/cloud-sql/main.tf` (new)
  - Potential supporting outputs/variables files under `infra/terraform/modules/cloud-sql/`
- **Backend**
  - `skate-assistant-backend/migrations/env.py` (update only if required)
  - `skate-assistant-backend/migrations/versions/*.py` (new initial revision)
  - `skate-assistant-backend/app/main.py` (startup drift guard)
  - `skate-assistant-backend/app/api/v1/ops.py` (schema version exposure if needed)
  - `skate-assistant-backend/tests/...` (migration + startup guard tests)
- **CI**
  - `.github/workflows/backend-ci.yml`
- **Docs**
  - `infra/README.md`
  - `docs/deploy.md`

### Existing Behavior To Preserve

- `/v1/health` and `/v1/readiness` endpoints exist and return structured JSON.
- Request correlation and structured logging format from Story 1.1 must remain unchanged.
- Existing CI stages (lint/type/unit/build/security) must still run; migration gate is additive, not replacement.
- Story 1.1 local-first workflow conventions and deferred cloud notes should remain explicit where cloud credentials are required.

### Technical Guardrails

- Do not introduce non-Alembic schema mutation paths.
- Do not bypass Terraform by manual cloud SQL setup in committed docs/code.
- Keep IAM least-privilege posture for DB access accounts.
- Avoid hardcoding secrets or credentials in repo files.
- Keep Python strictness (`mypy`, `ruff`) and deterministic dependency behavior from Story 1.1.

### Latest Technical Information (Web Research Snapshot)

- Alembic latest stable reported as `1.18.4` (2026-02) with ongoing async template support evolution.
- Async migration best practices remain:
  - async engine usage in env.py
  - `NullPool` for migration runtime
  - careful model import/metadata handling to avoid empty or incorrect revisions.
- Keep current project pinning strategy unless explicitly upgraded in this story with lockfile + CI verification.

### Testing Requirements

- Migration round-trip must be validated in CI and locally:
  - `upgrade head`
  - `downgrade -1`
  - `upgrade head`
- Add startup drift tests that prove service refusal on schema mismatch.
- Ensure readiness response reflects expected schema version once migration is active.

### Project Structure Notes

- Continue using monorepo paths already established in Story 1.1.
- New infra module(s) should follow current module style and naming conventions under `infra/terraform/modules/`.
- Migration files belong only under `skate-assistant-backend/migrations/versions/`.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` - Story 1.2 acceptance criteria]
- [Source: `_bmad-output/planning-artifacts/architecture.md` - constraints: Cloud SQL, Alembic mandatory, CI gates]
- [Source: `_bmad-output/planning-artifacts/prd.md` - API/error and integration governance]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` - continuity requirements for authenticated session journey]
- [Source: `_bmad-output/implementation-artifacts/1-1-project-foundation-and-gcp-infrastructure.md` - prior implementation patterns and fixes]

## Dev Agent Record

### Agent Model Used

gpt-5.3-codex

### Debug Log References

- Story target auto-discovered from sprint status first backlog item: `1-2-cloud-sql-provisioning-alembic-initial-schema-ci-gate`.
- Prior-story intelligence extracted from Story 1.1 artifact and recent commit patterns (`feat(story-1-1): foundation scaffolding + local-first dev stack`).
- Latest Alembic guidance cross-checked via web sources during context generation.
- Implemented Cloud SQL Terraform module and wired it into root Terraform composition with new variables and examples.
- Added startup schema compatibility check (`validate_schema_compatibility`) and health/readiness schema head reporting.
- Added Alembic initial migration `20260507_0001` for `audit_log`, with downgrade cleanup.
- Backend CI now provisions ephemeral Postgres service and runs migration gate: `upgrade -> downgrade -> upgrade`.
- Verification executed in backend package directory: `uv sync --frozen --dev`, `uv run ruff check`, `uv run ruff format --check .`, `uv run mypy app/ tests/`, `uv run pytest tests/unit -v --maxfail=1`, `uv run pytest -q`.
- Terraform CLI was unavailable in this runtime (`terraform: command not found`), so terraform validation was not executed locally in this session.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story is prepared for `dev-story` execution with AC-aligned tasks and architecture guardrails.
- Implemented AC1 with Cloud SQL primary + read replica IaC, private services networking, backup/PITR settings, and assistant DB users.
- Implemented AC2 with baseline Alembic revision and reversible downgrade path.
- Implemented AC3 with merge-blocking migration CI gate backed by deterministic Postgres service in GitHub Actions.
- Implemented AC4 with startup schema drift refusal logic and readiness schema version surfaced from Alembic head.
- Added targeted schema/migration tests and updated health expectations for Story 1.2.

### File List

- `.github/workflows/backend-ci.yml` (modified)
- `_bmad-output/implementation-artifacts/1-2-cloud-sql-provisioning-alembic-initial-schema-ci-gate.md` (modified)
- `docs/deploy.md` (modified)
- `infra/README.md` (modified)
- `infra/terraform/main.tf` (modified)
- `infra/terraform/modules/cloud-sql/main.tf` (new)
- `infra/terraform/modules/iam/main.tf` (modified)
- `infra/terraform/terraform.tfvars.example` (modified)
- `infra/terraform/variables.tf` (modified)
- `skate-assistant-backend/app/api/v1/ops.py` (modified)
- `skate-assistant-backend/app/main.py` (modified)
- `skate-assistant-backend/app/services/schema_version.py` (new)
- `skate-assistant-backend/migrations/versions/20260507_0001_initial_schema.py` (new)
- `skate-assistant-backend/tests/conftest.py` (modified)
- `skate-assistant-backend/tests/unit/test_health.py` (modified)
- `skate-assistant-backend/tests/unit/test_schema_version.py` (new)

## Change Log

- 2026-05-07: Implemented Story 1.2 end-to-end (Cloud SQL IaC, Alembic baseline migration, startup schema drift guard, CI migration gate, and tests). Story advanced to `review`.
