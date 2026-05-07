# Deferred Work

Items surfaced during reviews and dev cycles that have been intentionally deferred — not dismissed, not pre-existing problems we're ignoring. Tracked here so they don't get lost between stories.

## Deferred from: code review of story-1-1 (2026-05-07)

- **DE1 — WIF `attribute_condition` lacks `attribute.ref` constraint** — `infra/github/workload-identity.tf:55`. Apply-time concern; before any cloud deploy, scope the federation to `attribute.ref == "refs/heads/main"` for prod and split into a separate provider for staging. Story 1.1-cloud.
- **DE2 — `NEXT_PUBLIC_API_BASE_URL` won't work for SSR fetches inside docker network** — `docker-compose.yml:89`. From inside the frontend container, `localhost:8000` is the frontend itself, not the backend. Needs split into `INTERNAL_API_BASE_URL=http://backend:8080` for server-side fetches. Story 1.4 (when SSR calls land).
- **DE3 — `git_commit_sha` defaults to literal `"unknown"`** — `skate-assistant-backend/app/config.py:22`. CI sets `GIT_COMMIT_SHA` at build time, so this only leaks in local dev (intentional) — but worth a startup warning if running in `staging`/`prod` environments without it set.
- **DE4 — Empty-string defaults for required-in-prod secret references** — `skate-assistant-backend/app/config.py:33-37`. Loaders will validate at first use in Story 1.4+; consider a `model_validator` requiring non-empty when `environment in {"staging", "prod"}`.
- **DE5 — `migration-job` SA has zero role bindings** — `infra/terraform/modules/iam/main.tf:49-54`. Matrix-correct; `roles/cloudsql.client` lands with Cloud SQL provisioning in Story 1.2.
- **DE6 — VPC connector min/max instances at floor (200/300 Mbps)** — `infra/terraform/modules/network/main.tf:33-34`. Headroom for production traffic. Story 1.18 (pre-launch hardening).
- **DE7 — Secret Manager `replication: auto`** — `infra/terraform/modules/secrets/main.tf:26`. Auto replicates globally; data-residency decision pending. Switch to `user_managed` with explicit `replicas` blocks once compliance constraints are confirmed (and rotation cadence per secret is decided).
- **D6 — Frontend Dockerfile carries full `node_modules` (no `output: "standalone"`)** — `skate-assistant-frontend/Dockerfile`, `next.config.ts`. ~300MB image bloat on Cloud Run. Story 1.18 (pre-launch hardening) — currently local-dev only, so size doesn't matter today.

## Deferred from: code review of 1-3-design-system-foundation (2026-05-07)

- **No job dependency ensuring tests pass before Storybook runs** — `.github/workflows/frontend-ci.yml:61-92`. Storybook job runs in parallel with tests. Could merge failing code if tests fail but Storybook passes. Optimization not required by spec; consider for Story 1.18 hardening.
- **No cache strategy for Storybook build artifacts** — `.github/workflows/frontend-ci.yml:61-92`. Every run rebuilds Storybook from scratch. Could cache `storybook-static/` keyed by source hash. Performance optimization for future iteration.
- **Unused ts-expect-error directive in vitest config** — `skate-assistant-frontend/vitest.config.ts:6-7`. `@ts-expect-error` suppressing Vite type mismatch. May trigger unused-directive error once types align. Cleanup after Storybook/Vite types stabilize.
