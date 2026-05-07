# Deployment & Local Development

Story 1.1 ships a **local-first** development setup. The cloud paths (Cloud Run, Vercel, Cloud SQL) are codified but not yet executed — they activate when platform-team coordination and credentials land.

---

## Local development (works today)

```bash
# Full stack — postgres, redis, firebase emulator, backend, frontend
docker compose up

# Or just data plane while you `pnpm dev` / `uv run uvicorn` on the host
docker compose up postgres redis firebase-emulator
```

Service map (host ports):

| Service | Host port | Container port | Notes |
|---|---|---|---|
| Frontend (Next.js) | 3000 | 3000 | `pnpm dev` works standalone |
| Backend (FastAPI) | 8000 | 8080 | Container listens on 8080 |
| Postgres + pgvector | 5432 | 5432 | Schema lands in Story 1.2 |
| Redis | 6379 | 6379 | Memorystore swap in Story 1.13/1.14 |
| Firebase auth emulator | 9099 | 9099 | |
| Firestore emulator | 8080 | 8080 | |
| Firebase emulator UI | 4000 | 4000 | |

Smoke checks:

```bash
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/readiness
open http://localhost:3000
open http://localhost:4000        # Firebase emulator UI
```

Where logs/traces show up locally:

- **Logs:** structured JSON to stdout. `docker compose logs -f backend` to tail.
- **Traces:** with `OTEL_TRACES_EXPORTER=console` (the default in `.env.example`), spans print to stdout. Set `OTEL_TRACES_EXPORTER=gcp_trace` + `GOOGLE_CLOUD_PROJECT` once GCP creds are wired (Cloud Trace).

---

## Cloud deploy (deferred)

Activates when the platform team confirms:

- [ ] GCP project + billing for staging (and a separate project for prod, per architecture)
- [ ] Vercel team membership + GitHub-Vercel integration scope
- [ ] GitHub org / branch-protection ownership

### Apply order

1. **Bootstrap state bucket (out-of-band)**

   ```bash
   gcloud storage buckets create gs://<project-id>-terraform-state \
     --project=<project-id> --location=us-central1 \
     --uniform-bucket-level-access --enable-versioning
   ```

2. **Apply main IaC**

   ```bash
   cd infra/terraform
   cp terraform.tfvars.example terraform.tfvars   # fill in
   terraform init \
     -backend-config="bucket=<project-id>-terraform-state" \
     -backend-config="prefix=skate-assistant/staging"
   terraform plan
   terraform apply
   ```

   Verify with `gcloud`:

   ```bash
   gcloud iam service-accounts list --project <project-id>
   gcloud secrets list --project <project-id>
   gcloud artifacts repositories list --project <project-id>
   ```

3. **Wire GitHub OIDC**

   ```bash
   cd ../github
   terraform init -backend-config="bucket=<project-id>-terraform-state" \
                  -backend-config="prefix=skate-assistant/github-wif"
   terraform apply \
     -var="project_id=<project-id>" \
     -var="github_repository=<owner>/<repo>" \
     -var="ci_service_account_email=$(cd ../terraform && terraform output -raw ci_email)"
   ```

   Then in GitHub repo settings:
   - Add Action variables: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WORKLOAD_IDENTITY_PROVIDER` (output of step 3), `GCP_CI_SERVICE_ACCOUNT`.
   - Branch protection on `main`: require `backend-ci` and `frontend-ci` checks; require ≥ 1 review.

4. **Uncomment the `deploy-staging` job** in `.github/workflows/backend-ci.yml`. Push the first revision and verify in Cloud Run console.

5. **Vercel:** install the Vercel-GitHub integration on the org, point it at `skate-assistant-frontend/` with the working dir set, add `NEXT_PUBLIC_API_BASE_URL` env var pointing at the staging Cloud Run URL.

### Where things live (cloud)

- **Source repo:** `<org>/<repo>` (this monorepo)
- **Container images:** Artifact Registry — `<region>-docker.pkg.dev/<project-id>/skate-assistant-backend/`
- **Terraform state:** `gs://<project-id>-terraform-state/skate-assistant/staging/` (versioned, GCS-locked)
- **Logs:** Cloud Logging — filter by `resource.type="cloud_run_revision"`
- **Traces:** Cloud Trace — service `skate-assistant-backend`
- **Secrets:** Secret Manager — `firebase-admin-credentials`, `anthropic-api-key`, `langfuse-api-key`, `anonymous-jwt-signing-secret`

### Cloud Run service config (staging baseline — Story 1.18 tunes prod)

- Execution environment: **gen-2** (required for SSE timeouts in later stories)
- CPU: 2 vCPU, Memory: 4 GiB
- Concurrency per instance: 40
- Min instances: 0 (staging) / 2 (prod, set in Story 1.18)
- Max instances: 10 (staging) / 50 (prod)
- Request timeout: 60 minutes
- VPC connector: `skate-run-connector` (output of network module)
- Service account: `cloud-run-runtime`
