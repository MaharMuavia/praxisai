variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "environment" {
  type    = string
  default = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production"
  }
}
variable "web_image" { type = string }
variable "api_image" { type = string }
variable "database_name" {
  type    = string
  default = "praxisai"
}
variable "database_user" {
  type    = string
  default = "praxisai_app"
}
variable "credential_kms_enabled" {
  type    = bool
  default = false
}
variable "bigquery_enabled" {
  type    = bool
  default = false
}
variable "cloud_sql_tier" {
  type        = string
  default     = "db-f1-micro"
  description = "Cloud SQL tier. Use db-f1-micro or db-g1-small for staging, db-custom-1-3840 for production."
}
variable "vpc_name" {
  type    = string
  default = "praxisai-vpc"
}
variable "artifact_repository_id" {
  type    = string
  default = "praxisai"
}


