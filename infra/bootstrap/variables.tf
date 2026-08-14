variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "environment" {
  type    = string
  default = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production."
  }
}

variable "artifact_repository_id" {
  type    = string
  default = "praxisai"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository trusted to publish release images, in owner/name form."
  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must use the owner/name form."
  }
}

variable "github_repository_id" {
  type        = string
  description = "Immutable numeric GitHub repository ID trusted to publish release images."
  validation {
    condition     = can(regex("^[0-9]+$", var.github_repository_id))
    error_message = "github_repository_id must contain only decimal digits."
  }
}

variable "github_repository_owner_id" {
  type        = string
  description = "Immutable numeric GitHub repository owner ID trusted to publish release images."
  validation {
    condition     = can(regex("^[0-9]+$", var.github_repository_owner_id))
    error_message = "github_repository_owner_id must contain only decimal digits."
  }
}
