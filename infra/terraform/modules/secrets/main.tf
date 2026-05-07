# Secret Manager + placeholder secrets (empty versions added out-of-band).
# Rotation policies are intentionally not set here — confirm cadence per intake
# (firebase-admin-credentials: manual; anthropic-api-key: 90 days; jwt: 30 days).

variable "project_id" { type = string }
variable "region" { type = string }

resource "google_project_service" "secret_manager" {
  project            = var.project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

locals {
  secrets = [
    "firebase-admin-credentials",
    "anthropic-api-key",
    "langfuse-api-key",
    "anonymous-jwt-signing-secret",
  ]
}

resource "google_secret_manager_secret" "placeholders" {
  for_each = toset(local.secrets)

  project   = var.project_id
  secret_id = each.key

  replication {
    auto {}
  }

  depends_on = [google_project_service.secret_manager]
}

output "secret_ids" {
  value = { for s in google_secret_manager_secret.placeholders : s.secret_id => s.id }
}
