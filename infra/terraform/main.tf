locals {
  prefix = "praxisai-${var.environment}"
  required_services = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtasks.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com",
    "identityplatform.googleapis.com",
    "aiplatform.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
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

resource "google_compute_network" "vpc" {
  name                    = "${local.prefix}-${var.vpc_name}"
  auto_create_subnetworks = true
  depends_on              = [google_project_service.enabled_services]
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "${local.prefix}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

resource "google_sql_database_instance" "postgres" {
  name                = "${local.prefix}-postgres"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = true

  settings {
    tier              = var.cloud_sql_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_type         = "PD_SSD"
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "production"
    }
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
    insights_config {
      query_insights_enabled = true
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "app" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
}

resource "random_password" "database" {
  length  = 32
  special = true
}

resource "google_sql_user" "app" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.database.result
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
  secret_id  = "${local.prefix}-database-url"
  depends_on = [google_project_service.enabled_services]
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+asyncpg://${var.database_user}:${urlencode(random_password.database.result)}@/${var.database_name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
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
  depends_on          = [google_project_service.enabled_services]
  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = var.environment == "production" ? 1 : 0
      max_instance_count = var.environment == "production" ? 10 : 5
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance { instances = [google_sql_database_instance.postgres.connection_name] }
    }
    containers {
      image = var.api_image
      ports { container_port = 8080 }
      env { name = "APP_ENV" value = var.environment }
      env { name = "GOOGLE_CLOUD_PROJECT" value = var.project_id }
      env { name = "GOOGLE_CLOUD_LOCATION" value = var.region }
      env { name = "CLOUD_STORAGE_BUCKET" value = google_storage_bucket.artifacts.name }
      env { name = "CLOUD_TASKS_QUEUE" value = google_cloud_tasks_queue.jobs.name }
      env { name = "BIGQUERY_DATASET" value = var.bigquery_enabled ? google_bigquery_dataset.analytics[0].dataset_id : "" }
      env {
        name = "DATABASE_URL"
        value_source { secret_key_ref { secret = google_secret_manager_secret.database_url.secret_id, version = "latest" } }
      }
      env {
        name = "SESSION_SECRET"
        value_source { secret_key_ref { secret = google_secret_manager_secret.session_secret.secret_id, version = "latest" } }
      }
      env {
        name = "CSRF_SECRET"
        value_source { secret_key_ref { secret = google_secret_manager_secret.csrf_secret.secret_id, version = "latest" } }
      }
      volume_mounts { name = "cloudsql", mount_path = "/cloudsql" }
    }
  }
}

resource "google_cloud_run_v2_service" "web" {
  name                = "${local.prefix}-web"
  location            = var.region
  deletion_protection = var.environment == "production"
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
      env { name = "API_BASE_URL" value = google_cloud_run_v2_service.api.uri }
    }
  }
}

resource "google_project_iam_member" "api_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
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
        alignment_period    = "60s"
        per_series_aligner  = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }
}
