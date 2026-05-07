# Provider configuration.
# Authentication: Application Default Credentials (gcloud auth application-default login)
# or Workload Identity Federation in CI (see ../github/workload-identity.tf).

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ── Modules ─────────────────────────────────────────────────────────

module "network" {
  source = "./modules/network"

  project_id = var.project_id
  region     = var.region
  vpc_name   = "skate-assistant-vpc"
  subnet_cidr = "10.10.0.0/24"
}

module "secrets" {
  source = "./modules/secrets"

  project_id = var.project_id
  region     = var.region
}

module "artifact_registry" {
  source = "./modules/artifact-registry"

  project_id      = var.project_id
  region          = var.region
  repository_name = "skate-assistant-backend"
}

module "iam" {
  source = "./modules/iam"

  project_id = var.project_id
}
