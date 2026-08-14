# Configuration and secrets checklist

Do not send plaintext passwords, private keys, service-account JSON, or connection strings through
chat. Put them only in the local `.env` file or the deployment secret manager. `.env` is gitignored.

## Required now: Supabase database, Auth, private Storage, and local demo

These values configure the current application with Supabase PostgreSQL and private Supabase Storage:

| Value                                                         | Where to obtain it                                                  | Required handling                                                                                                            |
| ------------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Supabase transaction-pooler connection string                 | Supabase project database connection settings, normally port `6543` | Convert the scheme to `postgresql+asyncpg://` and set `DATABASE_URL`. Keep TLS parameters supplied by Supabase.              |
| Supabase session-pooler or reachable direct connection string | Supabase project database connection settings, normally port `5432` | Convert the scheme to `postgresql+asyncpg://` and set `DATABASE_MIGRATION_URL`. Alembic must not use the transaction pooler. |
| Supabase database password                                    | Chosen when creating/resetting the Supabase database                | URL-encode reserved characters before embedding it in the two connection strings. Never expose it to Next.js.                |
| Session secret                                                | Generate locally                                                    | At least 32 random characters in `SESSION_SECRET`.                                                                           |
| Session fallback secret                                       | Current/adjacent version of the same secret                         | Set `SESSION_SECRET_FALLBACK`; use the staged two-revision rotation in `docs/deployment.md`.                                  |
| Supabase project URL                                          | Supabase project settings                                           | Set `SUPABASE_URL` for the API and `NEXT_PUBLIC_SUPABASE_URL` for the browser; the URL is public configuration.              |
| Supabase publishable key                                      | Supabase project API settings                                       | Set `SUPABASE_PUBLISHABLE_KEY` for the API and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` for the browser; never substitute the service-role key. |
| Supabase service-role key                                     | Supabase project API settings                                      | Server-only `SUPABASE_SERVICE_ROLE_KEY`; never commit or expose it.                                                         |
| Private Storage bucket                                        | Created with `docs/supabase-storage.sql`                           | Set `SUPABASE_STORAGE_BUCKET`; keep the bucket private.                                                                     |

Set:

```dotenv
APP_ENV=local
DEMO_MODE=true
DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:ENCODED_PASSWORD@TRANSACTION_POOLER:6543/postgres
DATABASE_MIGRATION_URL=postgresql+asyncpg://postgres.PROJECT_REF:ENCODED_PASSWORD@SESSION_POOLER:5432/postgres
DATABASE_POOL_MODE=transaction
STORAGE_PROVIDER=supabase
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_PUBLISHABLE_KEY=PUBLIC_PROJECT_KEY
SUPABASE_SERVICE_ROLE_KEY=KEEP_THIS_SERVER_ONLY
SUPABASE_STORAGE_BUCKET=internship-submissions
IDENTITY_PROVIDER=supabase
NEXT_PUBLIC_SUPABASE_URL=https://PROJECT_REF.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=PUBLIC_PROJECT_KEY
SESSION_SECRET=GENERATE_A_RANDOM_VALUE_OF_AT_LEAST_32_CHARACTERS
SESSION_SECRET_FALLBACK=THE_SAME_VALUE_AS_SESSION_SECRET_UNTIL_A_STAGED_ROTATION
```

The server-side database connection does not require a Supabase Auth key. Supabase Auth token
verification requires the publishable key (or legacy anon key), while private Storage writes
require the server-only service-role key. Do not expose the service-role key to Next.js or students.

## Optional now: real Gemini instead of fixture AI

Choose one provider path:

1. Gemini Developer API: provide `GEMINI_API_KEY`, set `GEMINI_PROVIDER=gemini`, and identify the
   associated Google project in `GOOGLE_CLOUD_PROJECT`.
2. Vertex AI: provide `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`, authenticate the local
   machine with Application Default Credentials, and set `GEMINI_PROVIDER=gemini`.

No Gemini key is required while `GEMINI_PROVIDER=fixture` and the environment remains local/demo.
Never put a Gemini key in a `NEXT_PUBLIC_*` variable.

## Supabase Auth identity

The production identity provider is Supabase Auth. The browser uses the public project URL and
publishable key; the API verifies the short-lived access token through Supabase Auth, then links it
to the existing PraxisAI user and active membership tables. The service-role key is only for
server-side private Storage operations and must never be exposed to Next.js.

Required values:

- `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` (or legacy `SUPABASE_ANON_KEY`) for API identity verification;
- `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` for the browser;
- `SUPABASE_SERVICE_ROLE_KEY` only when private Storage is enabled;
- Supabase Auth email confirmation enabled for account provisioning.

## Hosted runtime dependencies

| Feature | Required value or resource | Current local behavior |
| --- | --- | --- |
| Private artifact storage | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_STORAGE_BUCKET` | Supabase Storage when `STORAGE_PROVIDER=supabase` |
| Production credential signing | Full CryptoKeyVersion in `CREDENTIAL_KMS_KEY_NAME` and KMS signer permission | Disposable gitignored demo key |
| Outbox and retention processing | Cloud Run job, Cloud Scheduler, runtime database URL, Supabase Storage secrets, and private ClamAV endpoint | `npm run worker:once` |
| Operational alerts | Operator email supplied to Terraform and Google Cloud Monitoring notification channel | Structured local logs |
| User notifications | No external email provider is claimed | In-app database notifications processed by the worker |

Hosted malware scanning requires `UPLOAD_SCANNER_PROVIDER=clamav` and a private,
authenticated network path from the worker to `CLAMAV_HOST:CLAMAV_PORT`. The
repository does not provision that external scanner or its network boundary; a
deployment is incomplete until the operator proves clean-file, rejection, and
scanner-failure behavior against the actual endpoint.

## Explicitly not required

- Stripe or any payment-processor key. PraxisAI currently records manually verified external
  funding and payout evidence.
- Cloud Run runtime configuration is managed by `infra/terraform`; operator-managed
  values belong in Google Secret Manager, not Terraform variables or Git.
- Firebase Authentication and Firebase browser configuration.
- Live Google Cloud resources for the local demo.

## What to provide to the project without exposing secrets

You can safely provide these non-secret identifiers when configuration work is requested:

- Supabase project reference;
- Supabase pooler hostname and region;
- whether the database is empty or already contains important data;
- Google Cloud project ID and preferred region;
- Supabase project reference and Auth settings;
- desired public web and API domains.

Keep every password, API key, signing key, and complete credential-bearing URL in your own `.env`
or secret manager. After editing `.env`, initialize and verify the database with:

```powershell
npm run db:migrate
npm run db:check
npm run seed:demo
npm run verify:demo
```
