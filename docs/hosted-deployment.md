# Hosted deployment contract

PraxisAI uses Supabase for managed PostgreSQL, Auth, and private object storage,
with Google Cloud for the application runtime. Cloud Run hosts the web and API
services plus a scheduled worker job. Secret Manager holds database URLs and
server secrets; Cloud Scheduler, Cloud Storage, Vertex AI, and Cloud KMS are
Google Cloud dependencies.

## State of the contract

| Capability | Repository state |
| --- | --- |
| Supabase PostgreSQL URL handling | Implemented in API settings and Terraform secret references |
| Browser-to-API same-origin routing | Implemented by the Next.js `/api/v1/[...path]` proxy |
| Private API service-to-service authentication | Implemented with same-origin web proxy, API `INGRESS_TRAFFIC_ALL`, and restricted Cloud Run invoker IAM; API is not granted `allUsers` invocation |
| Supabase browser build configuration | Implemented as explicit web image build arguments |
| Supabase Auth API configuration | Implemented with `IDENTITY_PROVIDER=supabase`, the project URL secret, and a public publishable-key Terraform variable |
| Notification, malware-scan, and short-term retention processing | Implemented as a least-privilege Cloud Run job invoked every two minutes by Cloud Scheduler |
| Database schema readiness | Implemented by comparing the deployed database revision with the repository Alembic head at `/ready` |
| State and image bootstrap | Implemented by `infra/bootstrap`: a versioned, protected GCS state bucket and immutable Artifact Registry repository |
| Hosted runtime validation | Implemented in API settings and web build validation |
| Terraform validation and container checks | CI configured; external execution must be verified in GitHub Actions |
| Supabase/GCP deployment | Not externally deployed or smoke-tested by this repository change |

## Supabase secrets

Create these Secret Manager secrets for each environment and add a version before
deploying Cloud Run. Do not put the values in Terraform variables or Git:

```text
postgresql+asyncpg://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@TRANSACTION_POOLER:6543/postgres
postgresql+asyncpg://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@SESSION_OR_DIRECT_HOST:5432/postgres
```

The transaction-pooler URL is `DATABASE_URL` for API and worker traffic. The
session or direct URL is `DATABASE_MIGRATION_URL` for the operator-run Alembic
step only; it is not injected into the web-facing API or worker. The password
must be URL encoded, including reserved characters such as `@`, `:`, `/`, and
`#`.

## Web image build arguments

Hosted web images require these public Supabase values at build time:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
NEXT_PUBLIC_APP_ENV=staging|production
NEXT_PUBLIC_DEMO_MODE=false
```

Supabase browser configuration is public application configuration, but the service-role key and
database passwords must never be passed as browser variables.

The API also requires `SUPABASE_PUBLISHABLE_KEY` at runtime to validate access
tokens through Supabase Auth. Terraform injects this browser-safe value from
`var.supabase_publishable_key`; it must identify the same project as the
`SUPABASE_URL` Secret Manager value used by the API.

## Evidence labels

- **Implemented** means code, Terraform, or tests exist in the repository.
- **Locally tested** means the command passed in the development environment.
- **CI verified** means the GitHub Actions run passed the corresponding job.
- **Externally deployed and smoke-tested** requires real Supabase, Cloud Run,
  Cloud Scheduler, KMS, Gemini/Vertex, private ClamAV, alert-delivery, backup,
  and rollback evidence; it is not claimed here.

## Cloud Run ingress and IAM boundary

The API uses `INGRESS_TRAFFIC_ALL` because Cloud Run's managed service-to-service
request path must be reachable without a Direct VPC egress design. This does not
make the API public: Terraform grants API `roles/run.invoker` only to the web
service account. The browser never receives the API URL and uses the web
`/api/v1` proxy, which strips browser-supplied forwarding and
service-authentication headers before adding the web service's OIDC identity.

The worker has a separate service account with access only to the runtime
database and the Supabase Storage secrets needed for notifications, malware
scanning, and retention. A separate scheduler identity can invoke only the
worker job. The migration database credential remains operator-only.

The authenticated `/api/v1/ops/integrations` view is a configuration inventory
augmented by recorded synchronization results; it is not a live provider probe.
Database schema readiness is reported only by `/ready`. Provider health claims
require the hosted smoke evidence listed in `docs/staging-smoke-report.md`.

The API error log sink writes to the private artifact bucket through an explicit
`roles/storage.objectCreator` grant for the sink writer identity. This is an IAM
configuration boundary, not evidence that a hosted deployment or smoke test has
completed.
