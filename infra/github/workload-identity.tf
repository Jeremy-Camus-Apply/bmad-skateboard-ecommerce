# GitHub Actions OIDC → GCP via Workload Identity Federation.
# Binds the GitHub repo to the `ci` service account so workflows authenticate
# without long-lived JSON keys.
#
# Apply this AFTER infra/terraform/ is applied (the `ci` SA must exist).
# Run from this directory:
#   terraform init -backend-config="bucket=<project-id>-terraform-state" \
#                  -backend-config="prefix=skate-assistant/github-wif"

terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {}
}

variable "project_id" { type = string }
variable "github_repository" {
  description = "GitHub repo in <owner>/<name> form (confirm with platform team)."
  type        = string
}
variable "ci_service_account_email" {
  description = "Email of the `ci` service account from terraform/modules/iam."
  type        = string
}

provider "google" {
  project = var.project_id
}

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-actions"
  display_name              = "GitHub Actions"
  description               = "Federated identity for repo CI"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.actor"      = "assertion.actor"
    "attribute.ref"        = "assertion.ref"
  }

  attribute_condition = "attribute.repository == \"${var.github_repository}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "ci_workload_identity" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.ci_service_account_email}"
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

output "workload_identity_provider" {
  description = "Use this in github/workflows as the `workload_identity_provider` input."
  value       = google_iam_workload_identity_pool_provider.github.name
}
