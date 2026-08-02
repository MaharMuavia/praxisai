# PraxisAI Staging Setup and Cost-Control Guide

This guide describes how to configure, operate, and tear down the PraxisAI staging environment on Google Cloud while keeping costs to an absolute minimum.

## Environment Architecture

- **Project ID**: `<PROJECT_ID>`
- **Region**: `<REGION>`
- **Gemini Location**: `global` (Vertex AI API)
- **Environment**: `staging`

## Staging Cost Minimization Design

To prevent unexpected billing charges during development and staging:

1. **Cloud Run**:
   - `min_instance_count = 0` (scales to zero when idle, incurring $0 compute cost).
   - `max_instance_count = 5` (caps scaling to prevent unexpected surges).
2. **Cloud SQL**:
   - Staging tier set to `db-f1-micro` (shared core, low monthly cost).
   - Public IPv4 disabled (`ipv4_enabled = false`) using private VPC networking.
3. **Optional Services**:
   - `bigquery_enabled = false` (avoids storage and slot charges in staging).
   - `credential_kms_enabled = false` (avoids monthly KMS active key version charges).
4. **Cloud Storage**:
   - Lifecycle rule configured to automatically delete staging artifacts older than 365 days.

## Inventory of Idle Charges

The table below documents resources and whether they accrue charges while idle:

| Component | Resource Type | Idle Charge Status | Cost Mitigation Strategy |
| --- | --- | --- | --- |
| Cloud Run | `google_cloud_run_v2_service` | **$0 / hour** ( scaled to 0 ) | `min_instance_count = 0` |
| Cloud SQL | `google_sql_database_instance` | **~$7 - $10 / month** | Low-cost tier `db-f1-micro` |
| Cloud Storage | `google_storage_bucket` | **$0 - $0.02 / GB / month** | Lifecycle auto-deletion rule |
| Secret Manager | `google_secret_manager_secret` | **$0** (within 6 free versions) | Clean up old secret versions |
| Cloud Tasks | `google_cloud_tasks_queue` | **$0** (within 1M free operations) | No background queue polling |
| Artifact Registry | `google_artifact_registry_repository` | **$0** (within 0.5 GB free storage) | Clean untagged images |
| KMS Key Ring | `google_kms_key_ring` | **$0** (when `credential_kms_enabled = false`) | Conditional variable |
| BigQuery Dataset | `google_bigquery_dataset` | **$0** (when `bigquery_enabled = false`) | Conditional variable |

## Environment Teardown Instructions

To completely destroy all staging resources and cease all billing:

1. Update `infra/terraform/main.tf` or set `deletion_protection = false` in staging tfvars for Cloud SQL and Cloud Run.
2. Execute the Terraform destroy command:

```bash
cd infra/terraform
terraform destroy -var-file="staging.tfvars"
```

3. Verify zero active instances in GCP Console for Cloud Run and Cloud SQL.
