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
variable "web_image" {
  type = string
  validation {
    condition     = can(regex("^.+@sha256:[0-9a-f]{64}$", var.web_image))
    error_message = "web_image must be an immutable image reference ending in @sha256:<64 lowercase hex characters>."
  }
}
variable "api_image" {
  type = string
  validation {
    condition     = can(regex("^.+@sha256:[0-9a-f]{64}$", var.api_image))
    error_message = "api_image must be an immutable image reference ending in @sha256:<64 lowercase hex characters>."
  }
}
variable "supabase_publishable_key" {
  type        = string
  description = "Public Supabase key used by the API to verify Auth access tokens."
  validation {
    condition     = trimspace(var.supabase_publishable_key) != ""
    error_message = "supabase_publishable_key must not be empty."
  }
}
variable "gemini_provider" {
  type    = string
  default = "gemini"
  validation {
    condition     = contains(["gemini"], var.gemini_provider)
    error_message = "gemini_provider must be gemini for hosted deployments."
  }
}
variable "gemini_model" {
  type    = string
  default = "gemini-2.5-flash"
}
variable "web_base_url" {
  type        = string
  description = "Public web URL used for API CORS and callback configuration."
  validation {
    condition = (
      can(regex("^https://[A-Za-z0-9.-]+(:[0-9]{1,5})?/?$", var.web_base_url)) &&
      !strcontains(lower(var.web_base_url), "localhost") &&
      !strcontains(var.web_base_url, "127.0.0.1")
    )
    error_message = "web_base_url must be an exact HTTPS origin without a path, query, credentials, or fragment."
  }
}
variable "cors_origins" {
  type        = list(string)
  description = "Exact browser origins allowed to call the API."
  validation {
    condition = (
      length(var.cors_origins) > 0 &&
      alltrue([
        for origin in var.cors_origins : (
          can(regex("^https://[A-Za-z0-9.-]+(:[0-9]{1,5})?/?$", origin)) &&
          !strcontains(lower(origin), "localhost") &&
          !strcontains(origin, "127.0.0.1")
        )
      ])
    )
    error_message = "cors_origins must contain only exact HTTPS origins."
  }
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
variable "database_url_secret_version" {
  type        = string
  description = "Pinned enabled Secret Manager version containing DATABASE_URL."
  validation {
    condition     = can(regex("^[1-9][0-9]*$", var.database_url_secret_version))
    error_message = "database_url_secret_version must be a positive numeric Secret Manager version."
  }
}
variable "supabase_url_secret_version" {
  type        = string
  description = "Pinned enabled Secret Manager version containing SUPABASE_URL."
  validation {
    condition     = can(regex("^[1-9][0-9]*$", var.supabase_url_secret_version))
    error_message = "supabase_url_secret_version must be a positive numeric Secret Manager version."
  }
}
variable "supabase_service_role_key_secret_version" {
  type        = string
  description = "Pinned enabled Secret Manager version containing the Supabase service-role key."
  validation {
    condition     = can(regex("^[1-9][0-9]*$", var.supabase_service_role_key_secret_version))
    error_message = "supabase_service_role_key_secret_version must be a positive numeric Secret Manager version."
  }
}
variable "session_secret_version" {
  type        = string
  description = "Pinned enabled Secret Manager version containing SESSION_SECRET."
  validation {
    condition     = can(regex("^[1-9][0-9]*$", var.session_secret_version))
    error_message = "session_secret_version must be a positive numeric Secret Manager version."
  }
}
variable "session_secret_fallback_version" {
  type        = string
  description = "Pinned enabled SESSION_SECRET version accepted only for session verification during staged rotation."
  validation {
    condition     = can(regex("^[1-9][0-9]*$", var.session_secret_fallback_version))
    error_message = "session_secret_fallback_version must be a positive numeric Secret Manager version."
  }
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
  description = "RFC1918 IPv4 address of the private ClamAV service reachable through worker Direct VPC egress."
  validation {
    # Unset at `terraform validate` time (no tfvars) is tolerated — apply still
    # requires the value. Only a *provided* value must be RFC1918.
    condition = var.clamav_host == null ? true : try(
      cidrhost("${var.clamav_host}/32", 0) == var.clamav_host &&
      (
        cidrcontains("10.0.0.0/8", var.clamav_host) ||
        cidrcontains("172.16.0.0/12", var.clamav_host) ||
        cidrcontains("192.168.0.0/16", var.clamav_host)
      ),
      false,
    )
    error_message = "clamav_host must be an RFC1918 IPv4 address; public clamd endpoints are forbidden."
  }
}
variable "clamav_port" {
  type    = number
  default = 3310
  validation {
    condition     = var.clamav_port >= 1 && var.clamav_port <= 65535
    error_message = "clamav_port must be between 1 and 65535."
  }
}
variable "worker_vpc_network" {
  type        = string
  description = "VPC network containing the private ClamAV endpoint."
  validation {
    condition     = trimspace(var.worker_vpc_network) != ""
    error_message = "worker_vpc_network must not be empty."
  }
}
variable "worker_vpc_subnetwork" {
  type        = string
  description = "Regional subnet used by Cloud Run Direct VPC egress and the private ClamAV endpoint."
  validation {
    condition     = trimspace(var.worker_vpc_subnetwork) != ""
    error_message = "worker_vpc_subnetwork must not be empty."
  }
}
variable "database_pool_mode" {
  type    = string
  default = "transaction"
  validation {
    condition     = var.database_pool_mode == "transaction"
    error_message = "database_pool_mode must be transaction for hosted Supabase deployments."
  }
}
variable "credential_kms_enabled" {
  type    = bool
  default = true
}
variable "credential_issuer" {
  type    = string
  default = "PraxisAI"
}
variable "alert_notification_email" {
  type        = string
  description = "Operator email address for Cloud Monitoring alerts."
  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_notification_email))
    error_message = "alert_notification_email must be a valid operator email address."
  }
}
variable "artifact_repository_id" {
  type    = string
  default = "praxisai"
}
