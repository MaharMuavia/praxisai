# PraxisAI Google Cloud deployment

This runbook deploys the Next.js web service, FastAPI service, and scheduled
background worker to Cloud Run. Supabase provides PostgreSQL, Auth, and private
Storage. Do not use `terraform apply` without operator review and approval.

## Prerequisites

- An authenticated `gcloud` CLI with permission to create the documented
  project resources.
- Terraform 1.8+, GitHub CLI, Docker Buildx, Node.js 22, Python 3.13, and `uv`.
- A Supabase project with email confirmation enabled and the private Storage
  bucket created from `docs/supabase-storage.sql`.
- An RFC1918 ClamAV endpoint in an existing VPC and regional subnet. Terraform
  configures worker Direct VPC egress and the `praxisai-worker` network tag;
  firewall ingress to clamd must allow only that tag/subnet. Clamd TCP is
  unencrypted, so a public endpoint is rejected by both configuration layers.
- The canonical HTTPS web origin selected before the first public deployment.

## 1. Bootstrap state and the release registry

The bootstrap module contains no application secrets. Its local state is
gitignored; protect the operator workstation because that state controls the
state bucket and registry.

```powershell
$repositoryMetadata = gh api repos/<OWNER>/<REPOSITORY> | ConvertFrom-Json
terraform -chdir=infra/bootstrap init -input=false
terraform -chdir=infra/bootstrap workspace select -or-create staging
terraform -chdir=infra/bootstrap fmt -check
terraform -chdir=infra/bootstrap validate
terraform -chdir=infra/bootstrap plan `
  -var="project_id=<PROJECT_ID>" `
  -var="environment=staging" `
  -var="github_repository=<OWNER>/<REPOSITORY>" `
  -var="github_repository_id=$($repositoryMetadata.id)" `
  -var="github_repository_owner_id=$($repositoryMetadata.owner.id)" `
  -out=bootstrap.tfplan
terraform -chdir=infra/bootstrap apply bootstrap.tfplan
```

Use a separate Terraform workspace for `production` so applying one Environment
does not replace the other's state bucket, registry, identity pool, or publisher.
Record `terraform_state_bucket`, `artifact_registry_repository_id`,
`docker_registry_host`, `github_workload_identity_provider`, and
`release_service_account` from the matching workspace outputs.

The registry rejects tag mutation. Production deployment inputs must be full
`repository@sha256:...` references.

## 2. Build the release artifacts once

Use the manually dispatched **Release container images** workflow. The local
`scripts/build_and_push.ps1` entry point is intentionally non-authoritative and
exits without building or pushing; a local tree or long-lived Google credential
must not become a release source.

Configure these non-secret variables on both protected GitHub Environments:

| Variable                               | Value                                                |
| -------------------------------------- | ---------------------------------------------------- |
| `GCP_PROJECT_ID`                       | Google Cloud project ID containing Artifact Registry |
| `GCP_REGION`                           | Artifact Registry region, for example `us-central1`  |
| `ARTIFACT_REPOSITORY`                  | `artifact_registry_repository_id` bootstrap output   |
| `GCP_WORKLOAD_IDENTITY_PROVIDER`       | `github_workload_identity_provider` bootstrap output |
| `GCP_RELEASE_SERVICE_ACCOUNT`          | `release_service_account` bootstrap output           |
| `NEXT_PUBLIC_SUPABASE_URL`             | Browser-safe Supabase project URL                    |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Browser-safe Supabase publishable key                |

The bootstrap provider checks the immutable numeric repository and owner IDs,
repository name, and GitHub Environment; production additionally requires
`refs/heads/main`. It grants the numeric repository principal
`roles/iam.workloadIdentityUser` on a dedicated service account and grants that
account only `roles/artifactregistry.writer` on the matching repository. Do not
create or store a service-account JSON key.
Restrict the `production` GitHub Environment to `main` and require an independent
reviewer; the workflow also rejects production dispatches from another ref.

Dispatch from the exact commit to release, select the environment, and enter the
same full 40-character commit in `release_sha`. The workflow builds each
production-mode image exactly once, pushes maximum provenance and SBOM
attestations, resolves the registry digests, and runs pinned Grype scans against
those exact Artifact Registry digests. It uploads checksummed manifests,
attestations, scan reports, metadata, and `terraform-images.tfvars` as
`release-<environment>-<sha>-<run-id>-<attempt>`.

Use only a successful, approved run. Verify the artifact's `SHA256SUMS`, review
both scan reports and both attestations, then copy the two digest-pinned values
from `terraform-images.tfvars` into a gitignored copy of the variables file:

```powershell
Copy-Item infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Set the canonical HTTPS `web_base_url`, matching `cors_origins`, public
Supabase publishable key, RFC1918 ClamAV address, worker VPC network/subnet, and
operator alert email. Never put a database URL, service-role key, session
secret, or other secret value in tfvars.

## 3. Initialize protected remote state

```powershell
terraform -chdir=infra/terraform init -reconfigure `
  -backend-config="bucket=<TERRAFORM_STATE_BUCKET>" `
  -backend-config="prefix=praxisai/staging"
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
```

Do not use `-backend=false` for a deployment. It is permitted only for CI
static validation. The remote GCS bucket supplies locking/version history; no
secret value belongs in Terraform state.

## 4. Create and populate Secret Manager containers

First create only the five secret containers from a saved, reviewed plan:

```powershell
terraform -chdir=infra/terraform plan `
  -var-file="terraform.tfvars" `
  -target=google_secret_manager_secret.database_url `
  -target=google_secret_manager_secret.database_migration_url `
  -target=google_secret_manager_secret.supabase_url `
  -target=google_secret_manager_secret.supabase_service_role_key `
  -target=google_secret_manager_secret.session_secret `
  -out=secrets-bootstrap.tfplan
terraform -chdir=infra/terraform apply secrets-bootstrap.tfplan
```

Add values using `gcloud secrets versions add --data-file` and local files
outside the repository:

- runtime Supabase transaction-pooler URL (`DATABASE_URL`);
- migration-only session/direct URL (`DATABASE_MIGRATION_URL`);
- HTTPS Supabase project URL;
- server-only Supabase service-role key;
- a session secret of at least 32 random characters.

Record the enabled numeric version for each runtime secret and set
`database_url_secret_version`, `supabase_url_secret_version`,
`supabase_service_role_key_secret_version`, `session_secret_version`, and
`session_secret_fallback_version` in the gitignored tfvars file. Initially both
session version inputs reference the same value. Runtime revisions never
resolve `latest`.

Rotate the session key in two revisions: first add the new version and deploy it
as the fallback while the current version stays unchanged; after that revision
is serving, deploy the new version as current and the old version as fallback.
This ensures both overlapping revisions accept both keys. After the eight-hour
session lifetime and all old revisions have drained, point fallback at current
and disable the old version.

The web-facing API and worker can read the runtime database secret. Neither can
read the migration credential; only the operator migration process receives it.

## 5. Back up and migrate before deploying new code

For an existing database, take and verify a restorable logical backup. Schedule
a maintenance window for locking DDL. Provide the two database URLs to the
migration process only, then run:

```powershell
npm run db:migrate
npm run db:current
npm run db:check
```

`db:current` must equal the repository's single Alembic head. The API startup
probe calls `/ready`, which checks both connectivity and the exact schema head;
a stale revision cannot receive traffic.

## 6. Review and apply the exact infrastructure plan

```powershell
terraform -chdir=infra/terraform plan `
  -var-file="terraform.tfvars" `
  -out=release.tfplan
terraform -chdir=infra/terraform show release.tfplan
```

After review and explicit operator approval, apply that exact saved plan:

```powershell
terraform -chdir=infra/terraform apply release.tfplan
```

Do not run a fresh unsaved `terraform apply`. Terraform deploys bounded Cloud
Run resources, schema-aware startup/liveness probes, a two-minute scheduled
worker with private VPC egress, and alert channels for API latency, API 5xx
responses, worker failures, and missing worker executions.

## 7. Smoke test and rollback

Verify through the public same-origin web route:

```powershell
Invoke-WebRequest "<WEB_URL>/api/v1/health"
Invoke-WebRequest "<WEB_URL>/api/v1/ready"
```

Then exercise real Supabase signup/email confirmation, session exchange,
private upload, ClamAV clean/reject behavior, worker execution, KMS credential
issue/verification, and a live Gemini workflow. Record Cloud Run revision, job
execution, image digests, and timestamps in `docs/staging-smoke-report.md`.

For an application regression, restore the previous digest references and
apply a reviewed plan. Do not Alembic-downgrade after new writes if the
downgrade removes data; roll forward or restore the verified backup under the
database incident procedure.
