# Supabase PostgreSQL setup

PraxisAI uses Supabase only as managed PostgreSQL. Supabase Auth, Storage, Edge Functions,
Realtime, and Row Level Security are not part of this integration; authorization remains in the
FastAPI service layer and PostgreSQL remains the transactional system of record.

See `database-schema.md` for the complete table map and `configuration-and-secrets.md` for the
credential checklist.

## Connection modes

Create a Supabase project and open **Project settings → Database → Connection string**. Keep the
password and complete connection strings outside the repository.

- Use the transaction pooler (normally port `6543`) for the deployed API. Set
  `DATABASE_POOL_MODE=transaction`; PraxisAI disables asyncpg prepared-statement caches and its
  local SQLAlchemy connection pool for compatibility with transaction pooling.
- Use the session pooler (normally port `5432`) or a reachable direct connection for Alembic.
  Set it as `DATABASE_MIGRATION_URL`. Do not run migrations through the transaction pooler.
- URL-encode characters such as `@`, `:`, `/`, `#`, and `%` in the database password.
- Keep TLS enabled in the connection strings supplied by the Supabase dashboard.

Example shape only:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:6543/postgres
DATABASE_MIGRATION_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres
DATABASE_POOL_MODE=transaction
```

## Initialize an empty project

If you prefer the Supabase SQL Editor, open [`supabase-schema.sql`](supabase-schema.sql),
copy the complete script, and run it once against a new empty project. It is generated from
the Alembic chain at head `c8f1a2d4e609` and includes the `alembic_version` marker. Do not run
it on a database that already has these tables; use the migration command below so only new
migrations are applied.

If `SELECT * FROM alembic_version;` already returns `fdeefd043d61`, the initial migration is
already installed. Use [`supabase-schema-from-initial.sql`](supabase-schema-from-initial.sql) in
the SQL Editor, or run `npm.cmd run db:migrate`; do not rerun the full schema export.

From the repository root, load the values through a local `.env`, then run:

```powershell
npm.cmd run db:migrate
npm.cmd run db:check
npm.cmd run seed:demo
npm.cmd run worker:once
npm.cmd run verify:demo
```

The seed command creates fictional records clearly marked as Demo data. Do not seed a production
database containing real commercial activity.

## Safety

- Do not expose the database URL through a `NEXT_PUBLIC_*` variable or browser code.
- Do not paste credentials into issues, chat, screenshots, deployment logs, or Terraform files.
- Rotate the database password if it is disclosed.
- Use Supabase backups appropriate to the selected plan before collecting real customer data.
- The free plan may pause or limit an inactive project; verify current Supabase limits before the
  judging period and keep an export/recovery plan.
