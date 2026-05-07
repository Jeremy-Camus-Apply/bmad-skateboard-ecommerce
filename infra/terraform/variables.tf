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

variable "cloud_sql_tier" {
  description = "Cloud SQL primary tier."
  type        = string
  default     = "db-custom-2-7680"
}

variable "cloud_sql_read_replica_tier" {
  description = "Cloud SQL read replica tier."
  type        = string
  default     = "db-custom-2-7680"
}

variable "cloud_sql_database_name" {
  description = "Assistant Cloud SQL database name."
  type        = string
  default     = "assistant"
}

variable "cloud_sql_deletion_protection" {
  description = "Protect Cloud SQL resources from accidental terraform destroy."
  type        = bool
  default     = true
}
