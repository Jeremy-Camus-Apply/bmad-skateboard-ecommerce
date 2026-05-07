# GCS state backend with object versioning enabled.
# The bucket "<project-id>-terraform-state" must be pre-created out-of-band
# (Subtask 1.2) before `terraform init`. Versioning + GCS lock provide state
# locking — no separate DynamoDB-equivalent needed.

terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    # Override at init time:
    #   terraform init \
    #     -backend-config="bucket=<project-id>-terraform-state" \
    #     -backend-config="prefix=skate-assistant/staging"
    #
    # Bucket variables intentionally not hardcoded so the same config
    # serves staging + prod without code duplication.
  }
}
