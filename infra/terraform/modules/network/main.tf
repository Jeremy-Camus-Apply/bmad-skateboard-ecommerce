# VPC + private subnet (/24) + Serverless VPC Access connector for Cloud Run egress.
# Subnet sized for Cloud Run + Cloud SQL + Memorystore reachability without overlap
# with the existing-platform network (confirm CIDR with platform team).

variable "project_id" { type = string }
variable "region" { type = string }
variable "vpc_name" { type = string }
variable "subnet_cidr" { type = string }

variable "connector_cidr" {
  description = "/28 CIDR for the Serverless VPC Access connector. Must not overlap subnet_cidr or any existing VPC subnet."
  type        = string
  default     = "10.20.0.0/28"
}

variable "connector_min_instances" {
  description = "Minimum connector instances. Floor is 2; production typically 3+."
  type        = number
  default     = 2
}

variable "connector_max_instances" {
  description = "Maximum connector instances. Must be > min_instances and <= 10."
  type        = number
  default     = 3
}

resource "google_compute_network" "vpc" {
  project                 = var.project_id
  name                    = var.vpc_name
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "private" {
  project                  = var.project_id
  name                     = "${var.vpc_name}-${var.region}"
  ip_cidr_range            = var.subnet_cidr
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Cloud Run egress to private services (Cloud SQL private IP, Memorystore).
resource "google_vpc_access_connector" "cloud_run" {
  project       = var.project_id
  name          = "skate-run-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = var.connector_cidr
  min_instances = var.connector_min_instances
  max_instances = var.connector_max_instances
}

output "vpc_id" { value = google_compute_network.vpc.id }
output "vpc_name" { value = google_compute_network.vpc.name }
output "subnet_id" { value = google_compute_subnetwork.private.id }
output "vpc_connector_id" { value = google_vpc_access_connector.cloud_run.id }
