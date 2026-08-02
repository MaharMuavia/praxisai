locals {
  prefix                           = "praxisai-${var.environment}"
  database_url_secret_id           = var.database_url_secret_id != "" ? var.database_url_secret_id : "${local.prefix}-database-url"
  database_migration_url_secret_id = var.database_migration_url_secret_id != "" ? var.database_migration_url_secret_id : "${local.prefix}-database-migration-url"
  required_services = [
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtasks.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com",
    "identityplatform.googleapis.com",
    "aiplatform.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]
}

resource "google_project_service" "enabled_services" {
  for_each           = toset(local.required_services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "google_service_account" "api" {
  account_id   = "${local.prefix}-api"
  display_name = "PraxisAI API (${var.environment})"
  depends_on   = [google_project_service.enabled_services]
}

resource "google_service_account" "web" {
  account_id   = "${local.prefix}-web"
  display_name = "PraxisAI web (${var.environment})"
  depends_on   = [google_project_service.enabled_services]
}

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "${local.prefix}-${var.artifact_repository_id}"
  description   = "Docker container images for PraxisAI"
  format        = "DOCKER"
  depends_on    = [google_project_service.enabled_services]
}

resource "random_password" "session_secret" {
  length  = 48
  special = false
}

resource "random_password" "csrf_secret" {
  length  = 48
  special = false
}

resource "google_secret_manager_secret" "database_url" {
  secret_id  = local.database_url_secret_id
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "database_migration_url" {
  secret_id  = local.database_migration_url_secret_id
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "session_secret" {
  secret_id  = "${local.prefix}-session-secret"
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "session_secret" {
  secret      = google_secret_manager_secret.session_secret.id
  secret_data = random_password.session_secret.result
}

resource "google_secret_manager_secret" "csrf_secret" {
  secret_id  = "${local.prefix}-csrf-secret"
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "csrf_secret" {
  secret      = google_secret_manager_secret.csrf_secret.id
  secret_data = random_password.csrf_secret.result
}

resource "google_storage_bucket" "artifacts" {
  name                        = "${var.project_id}-${local.prefix}-artifacts"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  versioning { enabled = true }
  lifecycle_rule {
    condition { age = 365 }
    action { type = "Delete" }
  }
  depends_on = [google_project_service.enabled_services]
}

resource "google_cloud_tasks_queue" "jobs" {
  name       = "${local.prefix}-jobs"
  location   = var.region
  depends_on = [google_project_service.enabled_services]
  retry_config {
    max_attempts       = 8
    max_retry_duration = "3600s"
    min_backoff        = "2s"
    max_backoff        = "300s"
  }
  rate_limits {
    max_concurrent_dispatches = 20
    max_dispatches_per_second = 10
  }
}

resource "google_bigquery_dataset" "analytics" {
  count                      = var.bigquery_enabled ? 1 : 0
  dataset_id                 = replace("${local.prefix}_analytics", "-", "_")
  location                   = var.region
  delete_contents_on_destroy = false
  depends_on                 = [google_project_service.enabled_services]
}

resource "google_kms_key_ring" "credentials" {
  count      = var.credential_kms_enabled ? 1 : 0
  name       = "${local.prefix}-credentials"
  location   = var.region
  depends_on = [google_project_service.enabled_services]
}

resource "google_kms_crypto_key" "credentials" {
  count    = var.credential_kms_enabled ? 1 : 0
  name     = "credential-signing"
  key_ring = google_kms_key_ring.credentials[0].id
  purpose  = "ASYMMETRIC_SIGN"
  version_template { algorithm = "RSA_SIGN_PKCS1_2048_SHA256" }
  lifecycle { prevent_destroy = true }
}

resource "google_identity_platform_config" "auth" {
  project                    = var.project_id
  autodelete_anonymous_users = true
  depends_on                 = [google_project_service.enabled_services]
  sign_in {
    email {
      enabled           = true
      password_required = true
    }
  }
}

resource "google_cloud_run_v2_service" "api" {
  name                = "${local.prefix}-api"
  location            = var.region
  deletion_protection = var.environment == "production"
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  depends_on          = [google_project_service.enabled_services]
  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = var.environment == "production" ? 1 : 0
      max_instance_count = var.environment == "production" ? 10 : 5
    }
    containers {
      image = var.api_image
      ports { container_port = 8080 }
      dynamic "env" {
        for_each = {
          APP_ENV                     = var.environment
          DEMO_MODE                   = "false"
          IDENTITY_PROVIDER           = "firebase"
          FIREBASE_PROJECT_ID         = var.firebase_project_id
          GEMINI_PROVIDER             = var.gemini_provider
          GEMINI_MODEL                = var.gemini_model
          GOOGLE_CLOUD_PROJECT        = var.project_id
          GOOGLE_CLOUD_LOCATION       = var.region
          COOKIE_SECURE               = "true"
          CORS_ORIGINS                = jsonencode(var.cors_origins)
          API_BASE_URL                = var.api_base_url
          WEB_BASE_URL                = var.web_base_url
          DATABASE_POOL_MODE          = var.database_pool_mode
          CREDENTIAL_SIGNING_PROVIDER = "kms"
          CREDENTIAL_KMS_KEY_NAME     = var.credential_kms_enabled ? google_kms_crypto_key.credentials[0].id : ""
          CREDENTIAL_ISSUER           = var.credential_issuer
          EMAIL_PROVIDER              = var.email_provider
          EMAIL_FROM_ADDRESS          = var.email_from_address
          OTEL_EXPORTER_OTLP_ENDPOINT = var.otel_exporter_otlp_endpoint
          CLOUD_STORAGE_BUCKET        = google_storage_bucket.artifacts.name
          CLOUD_TASKS_QUEUE           = google_cloud_tasks_queue.jobs.name
          BIGQUERY_DATASET            = var.bigquery_enabled ? google_bigquery_dataset.analytics[0].dataset_id : ""
          PAYMENT_PROVIDER            = "manual_external"
        }
        content {
          name  = env.key
          value = env.value
        }
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SESSION_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.session_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "CSRF_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.csrf_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DATABASE_MIGRATION_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_migration_url.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "web" {
  name                = "${local.prefix}-web"
  location            = var.region
  deletion_protection = var.environment == "production"
  ingress             = "INGRESS_TRAFFIC_ALL"
  depends_on          = [google_project_service.enabled_services]
  template {
    service_account = google_service_account.web.email
    scaling {
      min_instance_count = var.environment == "production" ? 1 : 0
      max_instance_count = var.environment == "production" ? 10 : 5
    }
    containers {
      image = var.web_image
      ports { container_port = 3000 }
      env {
        name  = "API_BASE_URL"
        value = google_cloud_run_v2_service.api.uri
      }
      env {
        name  = "APP_ENV"
        value = var.environment
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "NEXT_PUBLIC_APP_ENV"
        value = var.environment
      }
      env {
        name  = "NEXT_PUBLIC_DEMO_MODE"
        value = "false"
      }
    }
  }
}

resource "google_storage_bucket_iam_member" "api_artifacts" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_database" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_database_migration" {
  secret_id = google_secret_manager_secret.database_migration_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_session" {
  secret_id = google_secret_manager_secret.session_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_csrf" {
  secret_id = google_secret_manager_secret.csrf_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_tasks" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_v2_service_iam_member" "api_web_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.web.email}"
}

resource "google_cloud_run_v2_service_iam_member" "web_public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "terraform_data" "hosted_security_contract" {
  input = var.environment

  lifecycle {
    precondition {
      condition     = var.credential_kms_enabled
      error_message = "credential_kms_enabled must be true for staging and production."
    }
  }
}

resource "google_bigquery_dataset_iam_member" "api_analytics" {
  count      = var.bigquery_enabled ? 1 : 0
  dataset_id = google_bigquery_dataset.analytics[0].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.api.email}"
}

resource "google_kms_crypto_key_iam_member" "api_signer" {
  count         = var.credential_kms_enabled ? 1 : 0
  crypto_key_id = google_kms_crypto_key.credentials[0].id
  role          = "roles/cloudkms.signerVerifier"
  member        = "serviceAccount:${google_service_account.api.email}"
}

resource "google_logging_project_sink" "api_errors" {
  name                   = "${local.prefix}-api-errors-sink"
  destination            = "storage.googleapis.com/${google_storage_bucket.artifacts.name}"
  filter                 = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${google_cloud_run_v2_service.api.name}\" AND severity>=ERROR"
  unique_writer_identity = true
}

resource "google_monitoring_alert_policy" "api_latency" {
  display_name = "${local.prefix}-api-latency-alert"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run API Request Latency"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${google_cloud_run_v2_service.api.name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 2000
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }
}
