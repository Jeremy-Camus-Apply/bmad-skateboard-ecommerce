# Service accounts with least-privilege role bindings per the IAM Role Matrix
# in Story 1.1 Dev Notes. roles/owner / roles/editor / roles/iam.serviceAccountAdmin
# are NEVER granted here — escalate before adding any role not in the matrix.

variable "project_id" { type = string }
variable "enable_migration_cloudsql_role" {
  description = "Grant roles/cloudsql.client to migration-job SA when Cloud SQL is provisioned."
  type        = bool
  default     = false
}

# ── cloud-run-runtime ───────────────────────────────────────────────
resource "google_service_account" "cloud_run_runtime" {
  project      = var.project_id
  account_id   = "cloud-run-runtime"
  display_name = "Cloud Run runtime — assistant backend"
  description  = "Identity used by the FastAPI service at request time."
}

resource "google_project_iam_member" "cloud_run_runtime_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_runtime.email}"
}

# ── ci ──────────────────────────────────────────────────────────────
resource "google_service_account" "ci" {
  project      = var.project_id
  account_id   = "ci"
  display_name = "GitHub Actions CI"
  description  = "Used by GitHub Actions via Workload Identity Federation."
}

resource "google_project_iam_member" "ci_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/run.developer",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.ci.email}"
}

# ci needs to act-as cloud-run-runtime to deploy revisions.
resource "google_service_account_iam_member" "ci_can_actas_runtime" {
  service_account_id = google_service_account.cloud_run_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.ci.email}"
}

# ── migration-job ───────────────────────────────────────────────────
# SA is provisioned now; roles/cloudsql.client binding lands in Story 1.2
# when Cloud SQL is provisioned.
resource "google_service_account" "migration_job" {
  project      = var.project_id
  account_id   = "migration-job"
  display_name = "Alembic migration job"
  description  = "Runs Alembic migrations against Cloud SQL (Story 1.2+)."
}

resource "google_project_iam_member" "migration_job_cloudsql_client" {
  count = var.enable_migration_cloudsql_role ? 1 : 0

  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.migration_job.email}"
}

# ── Outputs ─────────────────────────────────────────────────────────
output "cloud_run_runtime_email" { value = google_service_account.cloud_run_runtime.email }
output "ci_email" { value = google_service_account.ci.email }
output "migration_job_email" { value = google_service_account.migration_job.email }
