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
variable "firebase_project_id" { type = string }
variable "gemini_provider" {
  type    = string
  default = "gemini"
}
variable "gemini_model" {
  type    = string
  default = "gemini-2.5-flash"
}
variable "web_base_url" {
  type        = string
  description = "Public web URL used for API CORS and callback configuration."
}
variable "api_base_url" {
  type        = string
  description = "API Cloud Run URL including /api/v1, used by API callbacks and tasks."
}
variable "cors_origins" {
  type        = list(string)
  description = "Exact browser origins allowed to call the API."
}
variable "database_url_secret_id" {
  type        = string
  default     = ""
  description = "Secret Manager secret containing the Supabase transaction-pooler URL."
}
variable "database_migration_url_secret_id" {
  type        = string
  default     = ""
  description = "Secret Manager secret containing the Supabase session/direct URL for migrations."
}
variable "supabase_url_secret_id" {
  type        = string
  default     = ""
  description = "Secret Manager secret containing the Supabase project URL."
}
variable "supabase_service_role_key_secret_id" {
  type        = string
  default     = ""
  description = "Secret Manager secret containing the Supabase server-only service-role key."
}
variable "supabase_storage_bucket" {
  type        = string
  default     = "internship-submissions"
  description = "Private Supabase Storage bucket used for uploaded artifacts."
}
variable "upload_scanner_provider" {
  type    = string
  default = "clamav"
  validation {
    condition     = contains(["disabled", "clamav"], var.upload_scanner_provider)
    error_message = "upload_scanner_provider must be disabled or clamav."
  }
}
variable "clamav_host" {
  type        = string
  description = "Reachable ClamAV service hostname for hosted upload scanning."
}
variable "clamav_port" {
  type    = number
  default = 3310
  validation {
    condition     = var.clamav_port >= 1 && var.clamav_port <= 65535
    error_message = "clamav_port must be between 1 and 65535."
  }
}
variable "database_pool_mode" {
  type    = string
  default = "transaction"
}
variable "credential_kms_enabled" {
  type    = bool
  default = true
}
variable "credential_issuer" {
  type    = string
  default = "PraxisAI"
}
variable "email_provider" {
  type    = string
  default = "sendgrid"
}
variable "email_from_address" { type = string }
variable "otel_exporter_otlp_endpoint" { type = string }
variable "bigquery_enabled" {
  type    = bool
  default = false
}
variable "artifact_repository_id" {
  type    = string
  default = "praxisai"
}
