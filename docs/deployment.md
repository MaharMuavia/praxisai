# PraxisAI Google Cloud Deployment Guide

This guide deploys the web and API containers to Cloud Run. Terraform provisions
Artifact Registry, Cloud Run, Secret Manager, Cloud Storage, Cloud Tasks, Firebase
Identity Platform, and the required IAM bindings. PostgreSQL and private upload
storage remain Supabase-managed services.

## Prerequisites

- `gcloud` CLI authenticated with permission to provision the listed services.
- Docker Desktop or another container engine with PowerShell integration.
- Terraform CLI v1.8.0+.
- Node.js 22+ and Python 3.12+.

## Deployment steps

### 1. Configure hosted inputs

Copy the example variables file and fill in the non-secret values:

```powershell
Copy-Item infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Use the exact HTTPS URLs configured for the web and API services. With custom
domains, use those domains. With default Cloud Run URLs, perform the first
Terraform apply from a reviewed plan, then set the resulting URLs in
`terraform.tfvars` and apply again.

Do not put database URLs or the Supabase service-role key in this file. Terraform
creates the Secret Manager containers; their values are added separately in step 3.

### 2. Build and push immutable container images

From PowerShell at the repository root:

```powershell
.\scripts\build_and_push.ps1 `
  -ProjectId "<PROJECT_ID>" `
  -Region "us-central1" `
  -Env "staging" `
  -FirebaseApiKey "<PUBLIC_FIREBASE_API_KEY>" `
  -FirebaseAuthDomain "<FIREBASE_PROJECT>.firebaseapp.com" `
  -FirebaseProjectId "<FIREBASE_PROJECT>" `
  -FirebaseStorageBucket "<FIREBASE_PROJECT>.appspot.com" `
  -FirebaseMessagingSenderId "<SENDER_ID>" `
  -FirebaseAppId "<FIREBASE_APP_ID>"
```

The script builds both images, tags them with the git commit SHA, pushes them to
the environment's Artifact Registry repository, and prints immutable image digests.
Firebase values are browser configuration, not server credentials.

Set `api_image` and `web_image` in `terraform.tfvars` to the digests printed by
the script. Set `clamav_host` to a reachable ClamAV service; hosted configuration
intentionally refuses to start with upload scanning disabled.

### 3. Bootstrap operator-managed secrets

Create the four operator-managed Secret Manager resources before the Cloud Run
revision is created:

```powershell
terraform -chdir=infra/terraform apply `
  -var-file="terraform.tfvars" `
  -target=google_secret_manager_secret.database_url `
  -target=google_secret_manager_secret.database_migration_url `
  -target=google_secret_manager_secret.supabase_url `
  -target=google_secret_manager_secret.supabase_service_role_key
```

Add each secret version with `gcloud secrets versions add --data-file`, using
local files that are not committed:

- `DATABASE_URL`: Supabase transaction-pooler URL;
- `DATABASE_MIGRATION_URL`: Supabase session/direct URL;
- `SUPABASE_URL`: Supabase project URL;
- `SUPABASE_SERVICE_ROLE_KEY`: server-only Supabase service-role key.

The secret IDs are printed by Terraform outputs. Do not put these values in
Terraform variables, source, or CI logs.

### 4. Plan and apply Terraform

```powershell
terraform -chdir=infra/terraform init -backend=false -input=false
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan -var-file="terraform.tfvars"
```

Review the plan, then apply it only with operator approval:

```powershell
terraform -chdir=infra/terraform apply -var-file="terraform.tfvars"
```

### 5. Run database migrations

Run migrations against Supabase using the migration URL from Secret Manager:

```powershell
npm run db:migrate
```

For a remote migration runner, provide `DATABASE_MIGRATION_URL` and
`DATABASE_URL` as temporary environment variables from the secret values. Never
copy them into source, Terraform variables, or CI logs.

### 6. Smoke test

After Cloud Run reports ready revisions, verify the public web URL and the API
health path through the same-origin web proxy:

```powershell
Invoke-WebRequest "<WEB_URL>/api/v1/health" | Select-Object StatusCode, Content
```

A live deployment is not considered verified until this request, authentication,
database readiness, upload scanning, and the relevant workflow smoke tests pass.
