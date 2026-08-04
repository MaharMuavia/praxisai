# Configuration and secrets checklist

Do not send plaintext passwords, private keys, service-account JSON, or connection strings through
chat. Put them only in the local `.env` file or the deployment secret manager. `.env` is gitignored.

## Required now: Supabase database, private Storage, and local demo

These values configure the current application with Supabase PostgreSQL and private Supabase Storage:

| Value                                                         | Where to obtain it                                                  | Required handling                                                                                                            |
| ------------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Supabase transaction-pooler connection string                 | Supabase project database connection settings, normally port `6543` | Convert the scheme to `postgresql+asyncpg://` and set `DATABASE_URL`. Keep TLS parameters supplied by Supabase.              |
| Supabase session-pooler or reachable direct connection string | Supabase project database connection settings, normally port `5432` | Convert the scheme to `postgresql+asyncpg://` and set `DATABASE_MIGRATION_URL`. Alembic must not use the transaction pooler. |
| Supabase database password                                    | Chosen when creating/resetting the Supabase database                | URL-encode reserved characters before embedding it in the two connection strings. Never expose it to Next.js.                |
| Session secret                                                | Generate locally                                                    | At least 32 random characters in `SESSION_SECRET`.                                                                           |
| CSRF secret                                                   | Generate locally                                                    | A different value of at least 32 random characters in `CSRF_SECRET`.                                                         |
| Supabase project URL                                          | Supabase project settings                                           | Server-only `SUPABASE_URL`; do not expose through `NEXT_PUBLIC_*`.                                                           |
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
SUPABASE_SERVICE_ROLE_KEY=KEEP_THIS_SERVER_ONLY
SUPABASE_STORAGE_BUCKET=internship-submissions
SESSION_SECRET=GENERATE_A_RANDOM_VALUE_OF_AT_LEAST_32_CHARACTERS
CSRF_SECRET=GENERATE_A_DIFFERENT_RANDOM_VALUE_OF_AT_LEAST_32_CHARACTERS
```

The server-side database connection does not require a Supabase anon key or browser key. Private
Storage writes do require the server-only service-role key. Do not expose it to Next.js or students.

## Optional now: real Gemini instead of fixture AI

Choose one provider path:

1. Gemini Developer API: provide `GEMINI_API_KEY`, set `GEMINI_PROVIDER=gemini`, and identify the
   associated Google project in `GOOGLE_CLOUD_PROJECT`.
2. Vertex AI: provide `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`, authenticate the local
   machine with Application Default Credentials, and set `GEMINI_PROVIDER=gemini`.

No Gemini key is required while `GEMINI_PROVIDER=fixture` and the environment remains local/demo.
Never put a Gemini key in a `NEXT_PUBLIC_*` variable.

## Optional later: production identity

The current demo uses environment-gated local identity. Production refuses that mode. The existing
production adapter uses Firebase Authentication and would require:

- `FIREBASE_PROJECT_ID` for server token verification;
- Firebase web configuration in the six `NEXT_PUBLIC_FIREBASE_*` variables;
- server Application Default Credentials or environment-gated credentials during local testing.

Supabase Auth is not currently integrated. Using it instead of Firebase is possible, but it requires
a separate identity-adapter implementation and tests; database connection keys alone do not enable
Supabase Auth.

## Optional later: storage, signing, jobs, and analytics

| Feature                       | Required value or resource                                         | Current local behavior              |
| ----------------------------- | ------------------------------------------------------------------ | ----------------------------------- |
| Private artifact storage      | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_STORAGE_BUCKET` | Supabase Storage when `STORAGE_PROVIDER=supabase` |
| Production credential signing | `CREDENTIAL_KMS_KEY_NAME` and KMS signer permission                | Disposable gitignored demo key      |
| Cloud Tasks outbox delivery   | `GOOGLE_CLOUD_PROJECT`, queue name, and task-enqueuer permission   | Local worker command                |
| BigQuery analytics            | Dataset configuration and writer permission                        | Disabled                            |
| Email notifications           | A future supported provider and credentials                        | Disabled; in-app notifications work |
| Observability exporter        | `OTEL_EXPORTER_OTLP_ENDPOINT` and provider credentials if required | Structured local logs               |

## Explicitly not required

- Stripe or any payment-processor key. PraxisAI currently records manually verified external
  funding and payout evidence.
- Cloud Run configuration while deployment remains deferred.
- Supabase browser keys for the current server-only PostgreSQL integration.
- Live Google Cloud resources for the local demo.

## What to provide to the project without exposing secrets

You can safely provide these non-secret identifiers when configuration work is requested:

- Supabase project reference;
- Supabase pooler hostname and region;
- whether the database is empty or already contains important data;
- Google Cloud project ID and preferred region;
- Firebase project ID if Firebase will be used;
- desired public web and API domains.

Keep every password, API key, signing key, and complete credential-bearing URL in your own `.env`
or secret manager. After editing `.env`, initialize and verify the database with:

```powershell
npm run db:migrate
npm run db:check
npm run seed:demo
npm run verify:demo
```
