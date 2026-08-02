output "api_url" {
  description = "URL of the API Cloud Run service"
  value       = google_cloud_run_v2_service.api.uri
}

output "web_url" {
  description = "URL of the Web Cloud Run service"
  value       = google_cloud_run_v2_service.web.uri
}

output "database_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "artifact_bucket" {
  description = "Private Cloud Storage artifact bucket name"
  value       = google_storage_bucket.artifacts.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository ID"
  value       = google_artifact_registry_repository.containers.id
}

output "vpc_network_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "cloud_tasks_queue" {
  description = "Cloud Tasks queue name"
  value       = google_cloud_tasks_queue.jobs.name
}

output "database_secret_id" {
  description = "Secret Manager secret ID for DATABASE_URL"
  value       = google_secret_manager_secret.database_url.secret_id
}

output "session_secret_id" {
  description = "Secret Manager secret ID for SESSION_SECRET"
  value       = google_secret_manager_secret.session_secret.secret_id
}

output "csrf_secret_id" {
  description = "Secret Manager secret ID for CSRF_SECRET"
  value       = google_secret_manager_secret.csrf_secret.secret_id
}

output "credential_key_name" {
  description = "Cloud KMS key name for credential signing"
  value       = var.credential_kms_enabled ? google_kms_crypto_key.credentials[0].id : null
}

output "bigquery_dataset_id" {
  description = "BigQuery analytics dataset ID"
  value       = var.bigquery_enabled ? google_bigquery_dataset.analytics[0].dataset_id : null
}
