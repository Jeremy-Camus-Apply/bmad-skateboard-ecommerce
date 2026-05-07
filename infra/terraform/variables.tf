variable "project_id" {
  description = "GCP project ID for the assistant (separate project per environment)."
  type        = string
}

variable "region" {
  description = "Primary GCP region. us-central1 is the documented default."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}
