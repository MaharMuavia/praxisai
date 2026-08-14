output "terraform_state_bucket" {
  description = "Protected GCS bucket for the main Terraform state."
  value       = google_storage_bucket.terraform_state.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository that receives release images."
  value       = google_artifact_registry_repository.containers.id
}

output "artifact_registry_repository_id" {
  description = "Repository ID to set as the ARTIFACT_REPOSITORY GitHub Environment variable."
  value       = google_artifact_registry_repository.containers.repository_id
}

output "docker_registry_host" {
  description = "Registry hostname to configure with gcloud auth configure-docker."
  value       = "${var.region}-docker.pkg.dev"
}

output "github_workload_identity_provider" {
  description = "Provider resource name to set as GCP_WORKLOAD_IDENTITY_PROVIDER."
  value       = google_iam_workload_identity_pool_provider.github_release.name
}

output "release_service_account" {
  description = "Publisher identity to set as GCP_RELEASE_SERVICE_ACCOUNT."
  value       = google_service_account.release_publisher.email
}
