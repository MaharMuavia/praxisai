# PraxisAI

PraxisAI connects practical learning to paid, supervised project work. Students build employer-relevant skills, record practice evidence, respond to complete project briefs with professional proposals, and carry selected work through verified delivery.

This repository contains an in-progress production-oriented MVP: a Next.js web application, a FastAPI transactional API, PostgreSQL persistence, structured learning paths, a student/employer talent marketplace, a Gemini adapter, audited external funding and payout evidence, and Google Cloud infrastructure definitions. No payment processor is integrated. Implemented vertical slices are tested; cloud deployment remains unverified. Demo records and fixture-provider output are always labeled **Demo data**.

## Core product loop

1. Students complete sequenced practice modules and record what they produced.
2. Employers publish paid opportunities with business context, deliverables, skills, budget, effort, timing, supervision, and proposal requirements.
3. Eligible students submit an immutable approach, milestone plan, work evidence, availability, delivery estimate, and price.
4. Employers compare proposals and record an accepted or rejected decision with a reason. Declines do not affect student reputation.
5. A selected proposal still passes scope, contract, supervision, and verified-funding gates before work starts.
6. Milestone evidence, QA, client acceptance, pay records, and credential evidence complete the professional record.

## Local setup

Requirements: Node.js 22+, Python 3.12+, `uv`, Docker, and Git.

1. Copy `.env.example` to `.env` and replace the local session secrets.
2. Run `docker compose up -d postgres`.
3. Run `npm run setup`.
4. Run `npm run seed:demo`.
5. Run `npm run worker:once` to deliver the seeded in-app notifications.
6. Run `npm run verify:demo` to verify signed credential and lifecycle evidence.
7. Run `npm run dev`, then open `http://localhost:3000`.

For a hosted database without Cloud SQL, follow
[`docs/supabase-setup.md`](docs/supabase-setup.md). Supabase is used only for PostgreSQL; server-side
PraxisAI authorization remains authoritative.

On Windows, use `npm.cmd` if PowerShell blocks `npm.ps1`. The Makefile mirrors the npm commands for environments with GNU Make.

## Safety defaults

- Local role switching and fixture agents run only in local/test or explicit demo mode.
- No payment processor is integrated. Coordinators may record independently verified external funding evidence; this does not initiate or claim settlement.
- Production credential issuance requires KMS; local credentials use a disposable gitignored key and are marked demo.
- PostgreSQL is authoritative. Analytics and notifications are asynchronous outbox consumers.
- Dead-letter recovery is idempotent and audited; every handler attempt has append-only history with secret-redacted errors.
- In-app notifications are delivered from dedicated outbox events, honor category preferences, and record provider synchronization evidence. Payment, credential, and appeal notices cannot be disabled.
- University metrics require an active agreement and consented enrollment. Cohorts below the configured minimum are suppressed, including exports.
- Credential revocation is append-only, and public verification checks the original signature plus revocation history.

See `docs/demo-script.md` for the shortest walkthrough and `docs/security-and-privacy.md` for trust boundaries.
The complete PostgreSQL table map is in `docs/database-schema.md`; required and optional credentials
are separated in `docs/configuration-and-secrets.md`.
Hosted deployment wiring and evidence requirements are documented in
[`docs/hosted-deployment.md`](docs/hosted-deployment.md).
