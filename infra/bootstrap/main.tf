locals {
  prefix = "praxisai-${var.environment}"
  bootstrap_services = toset([
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com",
  ])
}

resource "google_project_service" "bootstrap" {
  for_each           = local.bootstrap_services
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "google_storage_bucket" "terraform_state" {
  name                        = "${var.project_id}-${local.prefix}-tfstate"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 20
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [google_project_service.bootstrap]
}

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "${local.prefix}-${var.artifact_repository_id}"
  description   = "Immutable PraxisAI release container images"
  format        = "DOCKER"

  docker_config {
    immutable_tags = true
  }

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [google_project_service.bootstrap]
}

resource "google_iam_workload_identity_pool" "github_release" {
  project                   = var.project_id
  workload_identity_pool_id = "${local.prefix}-github"
  display_name              = "PraxisAI ${var.environment} releases"
  description               = "Repository- and environment-scoped identities for release image publication"

  depends_on = [google_project_service.bootstrap]
}

resource "google_iam_workload_identity_pool_provider" "github_release" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_release.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "${var.environment} release workflow"
  description                        = "Trusts only ${var.github_repository} ${var.environment} environment tokens"

  attribute_mapping = {
    "google.subject"                = "assertion.sub"
    "attribute.actor"               = "assertion.actor"
    "attribute.environment"         = "assertion.environment"
    "attribute.ref"                 = "assertion.ref"
    "attribute.repository"          = "assertion.repository"
    "attribute.repository_id"       = "assertion.repository_id"
    "attribute.repository_owner_id" = "assertion.repository_owner_id"
    "attribute.workflow_ref"        = "assertion.workflow_ref"
  }

  attribute_condition = var.environment == "production" ? (
    "assertion.repository == '${var.github_repository}' && assertion.repository_id == '${var.github_repository_id}' && assertion.repository_owner_id == '${var.github_repository_owner_id}' && assertion.environment == 'production' && assertion.ref == 'refs/heads/main' && assertion.workflow_ref == '${var.github_repository}/.github/workflows/release-images.yml@refs/heads/main'"
    ) : (
    "assertion.repository == '${var.github_repository}' && assertion.repository_id == '${var.github_repository_id}' && assertion.repository_owner_id == '${var.github_repository_owner_id}' && assertion.environment == 'staging' && assertion.workflow_ref.startsWith('${var.github_repository}/.github/workflows/release-images.yml@')"
  )

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "release_publisher" {
  project      = var.project_id
  account_id   = "${local.prefix}-release"
  display_name = "PraxisAI ${var.environment} release publisher"
  description  = "Publishes attested release images to the ${var.environment} repository"

  depends_on = [google_project_service.bootstrap]
}

resource "google_service_account_iam_member" "release_workload_identity" {
  service_account_id = google_service_account.release_publisher.name
  role               = "roles/iam.workloadIdentityUser"
  member = format(
    "principalSet://iam.googleapis.com/%s/attribute.repository_id/%s",
    google_iam_workload_identity_pool.github_release.name,
    var.github_repository_id,
  )

  depends_on = [google_iam_workload_identity_pool_provider.github_release]
}

resource "google_artifact_registry_repository_iam_member" "release_publisher" {
  project    = var.project_id
  location   = google_artifact_registry_repository.containers.location
  repository = google_artifact_registry_repository.containers.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.release_publisher.email}"
}
