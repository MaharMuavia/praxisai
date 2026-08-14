locals {
  prefix                              = "praxisai-${var.environment}"
  database_url_secret_id              = var.database_url_secret_id != "" ? var.database_url_secret_id : "${local.prefix}-database-url"
  database_migration_url_secret_id    = var.database_migration_url_secret_id != "" ? var.database_migration_url_secret_id : "${local.prefix}-database-migration-url"
  supabase_url_secret_id              = var.supabase_url_secret_id != "" ? var.supabase_url_secret_id : "${local.prefix}-supabase-url"
  supabase_service_role_key_secret_id = var.supabase_service_role_key_secret_id != "" ? var.supabase_service_role_key_secret_id : "${local.prefix}-supabase-service-role-key"
  required_services = [
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudkms.googleapis.com",
    "compute.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com",
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

data "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "${local.prefix}-${var.artifact_repository_id}"
}

resource "google_secret_manager_secret" "database_url" {
  secret_id  = local.database_url_secret_id
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
  lifecycle { prevent_destroy = true }
}

resource "google_secret_manager_secret" "database_migration_url" {
  secret_id  = local.database_migration_url_secret_id
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
  lifecycle { prevent_destroy = true }
}

resource "google_service_account" "worker" {
  account_id   = "${local.prefix}-worker"
  display_name = "PraxisAI background worker (${var.environment})"
  depends_on   = [google_project_service.enabled_services]
}

resource "google_service_account" "scheduler" {
  account_id   = "${local.prefix}-scheduler"
  display_name = "PraxisAI worker scheduler (${var.environment})"
  depends_on   = [google_project_service.enabled_services]
}

resource "google_secret_manager_secret" "supabase_url" {
  secret_id  = local.supabase_url_secret_id
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
  lifecycle { prevent_destroy = true }
}

resource "google_secret_manager_secret" "supabase_service_role_key" {
  secret_id  = local.supabase_service_role_key_secret_id
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
  lifecycle { prevent_destroy = true }
}

resource "google_secret_manager_secret" "session_secret" {
  secret_id  = "${local.prefix}-session-secret"
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
  lifecycle { prevent_destroy = true }
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
  lifecycle { prevent_destroy = true }
  depends_on = [google_project_service.enabled_services]
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

resource "google_kms_crypto_key_version" "credentials" {
  count      = var.credential_kms_enabled ? 1 : 0
  crypto_key = google_kms_crypto_key.credentials[0].id

  lifecycle { prevent_destroy = true }
}

resource "google_cloud_run_v2_service" "api" {
  name                = "${local.prefix}-api"
  location            = var.region
  deletion_protection = var.environment == "production"
  # The browser reaches this service through the authenticated same-origin web
  # proxy. Public ingress is required for Cloud Run's managed service-to-service
  # path; invocation remains restricted to the web service identity.
  ingress = "INGRESS_TRAFFIC_ALL"
  depends_on = [
    google_project_service.enabled_services,
    google_secret_manager_secret_iam_member.api_database,
    google_secret_manager_secret_iam_member.api_supabase_url,
    google_secret_manager_secret_iam_member.api_supabase_service_role_key,
    google_secret_manager_secret_iam_member.api_session,
  ]
  template {
    service_account                  = google_service_account.api.email
    timeout                          = "300s"
    max_instance_request_concurrency = 20
    scaling {
      min_instance_count = var.environment == "production" ? 1 : 0
      max_instance_count = var.environment == "production" ? 10 : 5
    }
    containers {
      image = var.api_image
      ports { container_port = 8080 }
      resources {
        limits = {
          cpu    = "2"
          memory = "1Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }
      startup_probe {
        initial_delay_seconds = 0
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 12
        http_get {
          path = "/ready"
          port = 8080
        }
      }
      liveness_probe {
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
        http_get {
          path = "/health"
          port = 8080
        }
      }
      dynamic "env" {
        for_each = {
          APP_ENV                     = var.environment
          DEMO_MODE                   = "false"
          IDENTITY_PROVIDER           = "supabase"
          SUPABASE_PUBLISHABLE_KEY    = var.supabase_publishable_key
          GEMINI_PROVIDER             = var.gemini_provider
          GEMINI_MODEL                = var.gemini_model
          GOOGLE_CLOUD_PROJECT        = var.project_id
          GOOGLE_CLOUD_LOCATION       = var.region
          COOKIE_SECURE               = "true"
          CORS_ORIGINS                = jsonencode(var.cors_origins)
          WEB_BASE_URL                = var.web_base_url
          DATABASE_POOL_MODE          = var.database_pool_mode
          CREDENTIAL_SIGNING_PROVIDER = "kms"
          CREDENTIAL_KMS_KEY_NAME     = var.credential_kms_enabled ? google_kms_crypto_key_version.credentials[0].name : ""
          CREDENTIAL_ISSUER           = var.credential_issuer
          STORAGE_PROVIDER            = "supabase"
          SUPABASE_STORAGE_BUCKET     = var.supabase_storage_bucket
          INTERNSHIP_MAX_UPLOAD_BYTES = tostring(30 * 1024 * 1024)
          UPLOAD_SCANNER_PROVIDER     = var.upload_scanner_provider
          CLAMAV_HOST                 = var.clamav_host
          CLAMAV_PORT                 = tostring(var.clamav_port)
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
            version = var.database_url_secret_version
          }
        }
      }
      env {
        name = "SESSION_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.session_secret.secret_id
            version = var.session_secret_version
          }
        }
      }
      env {
        name = "SESSION_SECRET_FALLBACK"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.session_secret.secret_id
            version = var.session_secret_fallback_version
          }
        }
      }
      env {
        name = "SUPABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.supabase_url.secret_id
            version = var.supabase_url_secret_version
          }
        }
      }
      env {
        name = "SUPABASE_SERVICE_ROLE_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.supabase_service_role_key.secret_id
            version = var.supabase_service_role_key_secret_version
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
    service_account                  = google_service_account.web.email
    timeout                          = "300s"
    max_instance_request_concurrency = 80
    scaling {
      min_instance_count = var.environment == "production" ? 1 : 0
      max_instance_count = var.environment == "production" ? 10 : 5
    }
    containers {
      image = var.web_image
      ports { container_port = 3000 }
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }
      env {
        name  = "API_BASE_URL"
        value = google_cloud_run_v2_service.api.uri
      }
      env {
        name  = "API_PROXY_TIMEOUT_MS"
        value = "300000"
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

resource "google_cloud_run_v2_job" "worker" {
  name                = "${local.prefix}-worker"
  location            = var.region
  deletion_protection = var.environment == "production"

  depends_on = [
    google_project_service.enabled_services,
    google_secret_manager_secret_iam_member.worker_database,
    google_secret_manager_secret_iam_member.worker_supabase_url,
    google_secret_manager_secret_iam_member.worker_supabase_service_role_key,
  ]

  template {
    task_count  = 1
    parallelism = 1
    template {
      service_account = google_service_account.worker.email
      timeout         = "1800s"
      max_retries     = 0
      vpc_access {
        egress = "PRIVATE_RANGES_ONLY"
        network_interfaces {
          network    = var.worker_vpc_network
          subnetwork = var.worker_vpc_subnetwork
          tags       = ["${local.prefix}-worker"]
        }
      }
      containers {
        image   = var.api_image
        command = ["python"]
        args    = ["-m", "app.worker", "--limit", "10"]
        resources {
          limits = {
            cpu    = "2"
            memory = "1Gi"
          }
        }
        dynamic "env" {
          for_each = {
            APP_ENV                     = var.environment
            APP_PROCESS_ROLE            = "worker"
            DEMO_MODE                   = "false"
            DATABASE_POOL_MODE          = var.database_pool_mode
            STORAGE_PROVIDER            = "supabase"
            SUPABASE_STORAGE_BUCKET     = var.supabase_storage_bucket
            UPLOAD_SCANNER_PROVIDER     = var.upload_scanner_provider
            CLAMAV_HOST                 = var.clamav_host
            CLAMAV_PORT                 = tostring(var.clamav_port)
            INTERNSHIP_MAX_UPLOAD_BYTES = tostring(30 * 1024 * 1024)
            OUTBOX_STALE_AFTER_SECONDS  = "2100"
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
              version = var.database_url_secret_version
            }
          }
        }
        env {
          name = "SUPABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.supabase_url.secret_id
              version = var.supabase_url_secret_version
            }
          }
        }
        env {
          name = "SUPABASE_SERVICE_ROLE_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.supabase_service_role_key.secret_id
              version = var.supabase_service_role_key_secret_version
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_job_iam_member" "worker_scheduler_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "worker" {
  name             = "${local.prefix}-worker"
  description      = "Process PraxisAI notification, malware scan, and retention outbox jobs"
  region           = var.region
  schedule         = "*/2 * * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "60s"

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_doublings        = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.worker.name}:run"
    body        = base64encode("{}")
    headers = {
      "Content-Type" = "application/json"
    }
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [
    google_project_service.enabled_services,
    google_cloud_run_v2_job.worker,
    google_cloud_run_v2_job_iam_member.worker_scheduler_invoker,
  ]
}

resource "google_secret_manager_secret_iam_member" "api_database" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "worker_database" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_secret_manager_secret_iam_member" "api_supabase_url" {
  secret_id = google_secret_manager_secret.supabase_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "worker_supabase_url" {
  secret_id = google_secret_manager_secret.supabase_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_secret_manager_secret_iam_member" "api_supabase_service_role_key" {
  secret_id = google_secret_manager_secret.supabase_service_role_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "worker_supabase_service_role_key" {
  secret_id = google_secret_manager_secret.supabase_service_role_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_secret_manager_secret_iam_member" "api_session" {
  secret_id = google_secret_manager_secret.session_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
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
    precondition {
      condition     = var.gemini_provider == "gemini"
      error_message = "gemini_provider must be gemini for staging and production."
    }
    precondition {
      condition     = var.upload_scanner_provider == "clamav"
      error_message = "upload_scanner_provider must be clamav for staging and production."
    }
    precondition {
      condition     = var.database_pool_mode == "transaction"
      error_message = "database_pool_mode must be transaction for the hosted Supabase runtime."
    }
    precondition {
      condition = startswith(
        var.api_image,
        "${var.region}-docker.pkg.dev/${var.project_id}/${data.google_artifact_registry_repository.containers.repository_id}/api@sha256:",
      )
      error_message = "api_image must be the digest-pinned API image from the bootstrapped Artifact Registry repository."
    }
    precondition {
      condition = startswith(
        var.web_image,
        "${var.region}-docker.pkg.dev/${var.project_id}/${data.google_artifact_registry_repository.containers.repository_id}/web@sha256:",
      )
      error_message = "web_image must be the digest-pinned web image from the bootstrapped Artifact Registry repository."
    }
  }
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

resource "google_storage_bucket_iam_member" "api_error_sink_writer" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.api_errors.writer_identity
}

resource "google_monitoring_alert_policy" "api_latency" {
  display_name = "${local.prefix}-api-latency-alert"
  combiner     = "OR"
  notification_channels = [
    google_monitoring_notification_channel.operator_email.name,
  ]
  conditions {
    display_name = "Cloud Run API Request Latency"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.project_id = \"${var.project_id}\" AND resource.labels.location = \"${var.region}\" AND resource.labels.service_name = \"${google_cloud_run_v2_service.api.name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
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

resource "google_monitoring_alert_policy" "api_server_errors" {
  display_name = "${local.prefix}-api-server-error-alert"
  combiner     = "OR"
  notification_channels = [
    google_monitoring_notification_channel.operator_email.name,
  ]
  conditions {
    display_name = "Cloud Run API 5xx responses"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.project_id = \"${var.project_id}\" AND resource.labels.location = \"${var.region}\" AND resource.labels.service_name = \"${google_cloud_run_v2_service.api.name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
      trigger { count = 1 }
    }
  }
}

resource "google_monitoring_alert_policy" "worker_failures" {
  display_name = "${local.prefix}-worker-failure-alert"
  combiner     = "OR"
  notification_channels = [
    google_monitoring_notification_channel.operator_email.name,
  ]
  conditions {
    display_name = "Cloud Run worker failed execution"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_job\" AND resource.labels.project_id = \"${var.project_id}\" AND resource.labels.location = \"${var.region}\" AND resource.labels.job_name = \"${google_cloud_run_v2_job.worker.name}\" AND metric.type = \"run.googleapis.com/job/completed_execution_count\" AND metric.labels.result = \"failed\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
      trigger {
        count = 1
      }
    }
  }
}

resource "google_monitoring_alert_policy" "worker_execution_absent" {
  display_name = "${local.prefix}-worker-execution-absent-alert"
  combiner     = "OR"
  notification_channels = [
    google_monitoring_notification_channel.operator_email.name,
  ]
  conditions {
    display_name = "Cloud Run worker has no completed execution"
    condition_absent {
      filter   = "resource.type = \"cloud_run_job\" AND resource.labels.project_id = \"${var.project_id}\" AND resource.labels.location = \"${var.region}\" AND resource.labels.job_name = \"${google_cloud_run_v2_job.worker.name}\" AND metric.type = \"run.googleapis.com/job/completed_execution_count\""
      duration = "900s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
      trigger { count = 1 }
    }
  }
}

resource "google_monitoring_notification_channel" "operator_email" {
  display_name = "${local.prefix} operator email"
  type         = "email"
  labels = {
    email_address = var.alert_notification_email
  }
  lifecycle { prevent_destroy = true }
  depends_on = [google_project_service.enabled_services]
}
