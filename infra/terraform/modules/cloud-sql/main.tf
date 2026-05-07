variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

variable "network_self_link" {
  description = "Self-link of the VPC used for private services access."
  type        = string
}

variable "db_tier" {
  description = "Primary Cloud SQL machine tier."
  type        = string
  default     = "db-custom-2-7680"
}

variable "read_replica_tier" {
  description = "Read replica machine tier."
  type        = string
  default     = "db-custom-2-7680"
}

variable "database_version" {
  description = "Cloud SQL PostgreSQL major version."
  type        = string
  default     = "POSTGRES_16"
}

variable "database_name" {
  description = "Application database name."
  type        = string
  default     = "assistant"
}

variable "deletion_protection" {
  description = "Whether instances are protected from accidental deletion."
  type        = bool
  default     = true
}

resource "google_project_service" "service_networking" {
  project = var.project_id
  service = "servicenetworking.googleapis.com"
}

resource "google_project_service" "sqladmin" {
  project = var.project_id
  service = "sqladmin.googleapis.com"
}

resource "google_compute_global_address" "private_service_range" {
  project       = var.project_id
  name          = "skate-assistant-sql-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.network_self_link
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = var.network_self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_range.name]

  depends_on = [google_project_service.service_networking]
}

resource "google_sql_database_instance" "primary" {
  project          = var.project_id
  name             = "skate-assistant-pg-primary"
  region           = var.region
  database_version = var.database_version

  deletion_protection = var.deletion_protection

  settings {
    tier              = var.db_tier
    availability_type = "REGIONAL"

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_self_link
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = 35
        retention_unit   = "COUNT"
      }
    }
  }

  depends_on = [
    google_project_service.sqladmin,
    google_service_networking_connection.private_vpc_connection,
  ]
}

resource "google_sql_database_instance" "read_replica" {
  project             = var.project_id
  name                = "skate-assistant-pg-read-replica"
  region              = var.region
  database_version    = var.database_version
  master_instance_name = google_sql_database_instance.primary.name
  deletion_protection = var.deletion_protection

  replica_configuration {
    failover_target = false
  }

  settings {
    tier = var.read_replica_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_self_link
    }
  }
}

resource "google_sql_database" "assistant" {
  project  = var.project_id
  name     = var.database_name
  instance = google_sql_database_instance.primary.name
}

resource "google_sql_user" "assistant_read_only" {
  project  = var.project_id
  instance = google_sql_database_instance.primary.name
  name     = "assistant_read_only"
}

resource "google_sql_user" "assistant_read_write" {
  project  = var.project_id
  instance = google_sql_database_instance.primary.name
  name     = "assistant_read_write"
}

output "primary_instance_name" {
  value = google_sql_database_instance.primary.name
}

output "primary_connection_name" {
  value = google_sql_database_instance.primary.connection_name
}

output "primary_private_ip" {
  value = google_sql_database_instance.primary.private_ip_address
}

output "read_replica_instance_name" {
  value = google_sql_database_instance.read_replica.name
}

output "database_name" {
  value = google_sql_database.assistant.name
}
