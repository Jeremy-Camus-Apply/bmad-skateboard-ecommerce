# Artifact Registry Docker repo for backend container images.

variable "project_id" { type = string }
variable "region" { type = string }
variable "repository_name" { type = string }

resource "google_project_service" "artifact_registry" {
  project            = var.project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "backend" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_name
  description   = "Skate Assistant backend container images"
  format        = "DOCKER"

  # KEEP rules win over DELETE — scope keep-last-10 to TAGGED versions so it
  # doesn't accidentally preserve untagged images that the next policy targets.
  cleanup_policies {
    id     = "keep-last-10-tagged"
    action = "KEEP"
    most_recent_versions {
      package_name_prefixes = ["api"]
      keep_count            = 10
    }
  }

  cleanup_policies {
    id     = "delete-untagged-after-7d"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "604800s"
    }
  }

  depends_on = [google_project_service.artifact_registry]
}

output "repository_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}"
}
