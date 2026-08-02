# PraxisAI Google Cloud Deployment Guide

This guide details the deployment of PraxisAI to Google Cloud using Terraform, Cloud Run, Cloud SQL, Secret Manager, Cloud Storage, Cloud Tasks, and Firebase Identity Platform.

## Prerequisites

- `gcloud` CLI authenticated with Project Owner/Editor privileges.
- Docker Desktop or container engine with PowerShell integration.
- Terraform CLI (v1.8.0+).
- Node.js 22+ and Python 3.12+.

## Deployment Steps

### 1. Build and Push Container Images

From PowerShell in the repository root, run the image build and push script:

```powershell
.\scripts\build_and_push.ps1 -ProjectId "<PROJECT_ID>" -Region "<REGION>" -Repository "praxisai-staging-praxisai" -Env "staging"
```

The script builds both `web` and `api` Docker images, tags them with the git commit SHA, pushes them to Google Artifact Registry, and prints the immutable image digests.

### 2. Configure Terraform Variables

Copy `infra/terraform/terraform.tfvars.example` to `infra/terraform/terraform.tfvars`:

```hcl
project_id             = "<PROJECT_ID>"
region                 = "<REGION>"
environment            = "staging"
api_image              = "us-central1-docker.pkg.dev/<PROJECT_ID>/praxisai-staging-praxisai/api@sha256:<API_IMAGE_DIGEST>"
web_image              = "us-central1-docker.pkg.dev/<PROJECT_ID>/praxisai-staging-praxisai/web@sha256:<WEB_IMAGE_DIGEST>"
cloud_sql_tier         = "db-f1-micro"
bigquery_enabled       = false
credential_kms_enabled = false
```

### 3. Validate Terraform Configuration

```bash
cd infra/terraform
terraform init -backend=false
terraform validate
```

> [!NOTE]
> Do not execute `terraform apply` without operator review and approval.

### 4. Database Migrations

Run database migrations against Cloud SQL using the Cloud SQL Auth Proxy or temporary migration job:

```bash
npm run db:migrate
```

### 5. Runtime Secrets Setup

Secrets are automatically managed in Google Secret Manager (`database-url`, `session-secret`, `csrf-secret`) and injected securely into Cloud Run containers via Secret Manager volume/environment references.
