# Hosted deployment contract

PraxisAI uses Supabase as managed PostgreSQL and Google Cloud for the application
runtime. Cloud Run hosts the web and API services; Secret Manager holds database
URLs and server secrets; Cloud Tasks, Cloud Storage, Vertex AI, and Cloud KMS are
Google Cloud dependencies.

## State of the contract

| Capability | Repository state |
| --- | --- |
| Supabase PostgreSQL URL handling | Implemented in API settings and Terraform secret references |
| Browser-to-API same-origin routing | Implemented by the Next.js `/api/v1/[...path]` proxy |
| Private API service-to-service authentication | Implemented in the proxy and Terraform IAM |
| Firebase browser build configuration | Implemented as explicit web image build arguments |
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

The transaction-pooler URL is `DATABASE_URL` for runtime traffic. The session or
direct URL is `DATABASE_MIGRATION_URL` for Alembic. The password must be URL
encoded, including reserved characters such as `@`, `:`, `/`, and `#`.

## Web image build arguments

Hosted web images require these public Firebase values at build time:

```text
NEXT_PUBLIC_FIREBASE_API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
NEXT_PUBLIC_FIREBASE_PROJECT_ID
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
NEXT_PUBLIC_FIREBASE_APP_ID
NEXT_PUBLIC_APP_ENV=staging|production
NEXT_PUBLIC_DEMO_MODE=false
```

Firebase browser configuration is public application configuration, but server
credentials and Supabase database passwords must never be passed as browser
variables.

## Evidence labels

- **Implemented** means code, Terraform, or tests exist in the repository.
- **Locally tested** means the command passed in the development environment.
- **CI verified** means the GitHub Actions run passed the corresponding job.
- **Externally deployed and smoke-tested** requires real Supabase, GCP, Firebase,
  KMS, email, telemetry, and Cloud Run evidence; it is not claimed here.
