# Core product hardening plan

Baseline: `agent/core-product-completion` at `093a186`.

## CI failure found before editing

- Severity: P0
- User impact: PR #4 cannot reach any application quality gate.
- Root cause: Alembic autogenerate sees a mismatch between the model's unique index and the migration's non-unique index plus table-level unique constraint on `public_intake_submissions.idempotency_key`.
- Current implementation: `apps/api/alembic/versions/a7f1c2d3e4b5_add_public_intake_submissions.py` creates both a unique constraint and a non-unique index; the model declaration creates a unique model-owned index.
- Correct implementation: Use one model/migration representation: a unique index owned by the model and migration, with no duplicate table constraint.
- Files affected: intake model, intake migration.
- Tests required: Alembic upgrade/check and OpenAPI drift checks.
- Final verification result: migration definition now uses one unique index; local Alembic check is unverified because PostgreSQL is not reachable.

## Hardening issues

### 1. Route ownership and shell scope

- Severity: P0
- User impact: Page data, mutations, loading, and errors remain coupled in `AppShell`; `/ops/intake` cannot be operated as a real feature.
- Root cause: explicit pages delegate to `WorkspaceRoute`, which delegates to `AppShell`; `useWorkspaceData` still owns cross-route fetches.
- Current implementation: `apps/web/components/app-shell.tsx`, `apps/web/components/workspace/workspace-route.tsx`, `apps/web/components/workspace/use-workspace-data.ts`.
- Correct implementation: shared layouts own only session/shell concerns; feature pages own their query, mutation, and state modules.
- Files affected: `apps/web/app/(workspace)`, `apps/web/features`, shell/layout components, query modules.
- Tests required: route isolation, loading/error/empty/permission states, operations intake flows.
- Final verification result: `/ops/intake` and `/ops/intake/[submissionId]` now render a queue/detail feature with its own queries, mutations, and permission states; broader legacy routes remain on the compatibility shell.

### 2. Operations intake interface

- Severity: P0
- User impact: staff can call an endpoint but cannot safely review or manage submissions through the product.
- Root cause: only API queue/review routes exist; no queue/detail UI, filters, pagination, owner picker, or transition feedback exists.
- Current implementation: `apps/api/app/api/intake.py` and `apps/web/app/(workspace)/ops/intake/page.tsx`.
- Correct implementation: accessible queue and detail screens with protected mutations and audit-visible state.
- Files affected: `apps/web/features/intake`, ops routes, intake API/query modules.
- Tests required: queue filters, detail loading, review mutations, unauthorized access, owner validation.
- Final verification result: strict discriminated schemas, frontend fields, OpenAPI, and focused API/UI tests pass.

### 3. Strict intake contracts

- Severity: P0
- User impact: broad optional payloads permit wrong-kind fields and malformed contact data into a privacy-sensitive boundary.
- Root cause: one optional `PublicIntakeSubmissionCreate` model and string email validation.
- Current implementation: `apps/api/app/domain/schemas.py`.
- Correct implementation: discriminated strict schemas with `extra="forbid"`, `EmailStr`, normalized URL/email fields, and role-specific validation.
- Files affected: schemas, API route, frontend form, OpenAPI client.
- Tests required: all four valid kinds, extra fields, wrong-kind fields, invalid email/URL, consent, missing fields.
- Final verification result: stable client keys, payload hashes, conflict handling, trusted proxy parsing, and focused idempotency coverage are implemented; concurrent PostgreSQL execution is CI-only.

### 4. Idempotency, rate limits, and trusted IPs

- Severity: P0
- User impact: retries can consume rate limits, concurrent requests can race, and spoofed forwarding headers can poison abuse controls.
- Root cause: read-then-insert service, new frontend key per request, and direct `request.client.host` use.
- Current implementation: `apps/api/app/intake/service.py`, `apps/api/app/api/intake.py`, `apps/web/components/public-intake-form.tsx`.
- Correct implementation: stable logical keys, payload hashes, conflict recovery, resolve-before-rate-limit, deployment-aware trusted proxy parsing, and privacy-safe bucket keys.
- Files affected: intake service/API/model/migration, frontend form, proxy configuration docs.
- Tests required: sequential/concurrent same-key requests, mismatched payload 409, rate-limit ordering, trusted/spoofed proxy headers.
- Final verification result: transition map, required evidence/reasons, optimistic version, and active internal owner validation are implemented; full API suite passes.

### 5. Controlled workflow and ownership

- Severity: P0
- User impact: arbitrary status and owner updates can bypass review policy and create misleading audit history.
- Root cause: `PublicIntakeSubmissionUpdate` accepts any status string from a flat update endpoint and does not validate owner membership/state/version.
- Current implementation: `apps/api/app/intake/service.py` and `apps/api/app/api/intake.py`.
- Correct implementation: explicit transition state machine, expected-version checks, validated internal owners, conversion evidence, and complete audit payloads.
- Files affected: enums, schemas, service, API routes, migrations, tests.
- Tests required: valid/invalid transitions, stale version, reason/evidence requirements, owner access, audit uniqueness.
- Final verification result: retention metadata, daily-worker function, protected anonymization endpoint, audit event, and operator documentation are implemented.

### 6. Privacy retention and deletion

- Severity: P0
- User impact: personal and potentially sensitive intake data has no documented expiry, withdrawal, anonymization, or deletion operation.
- Root cause: model stores contact and payload without retention metadata or a scheduled privacy operation.
- Current implementation: `PublicIntakeSubmission` and its migration.
- Correct implementation: retention metadata, consent/purpose versioning, audited anonymization/deletion, and an operator-run retention job.
- Files affected: model/migration/service/API/worker, `docs/public-intake-privacy.md`.
- Tests required: deadline calculation, rejected-record policy, anonymization, withdrawal/deletion authorization, audit safety.
- Final verification result: intake direct detail access returns permission-aware UI states; action resolver and other legacy workspace routes remain unchanged in this pass.

### 7. Direct authorization and action quality

- Severity: P1
- User impact: filtered navigation does not prevent direct access, and primary actions can still be generic or self-linking.
- Root cause: route pages do not classify auth/permission/not-found/unavailable states; resolver has limited record context.
- Current implementation: workspace layouts, `lib/workspace-actions`, and `workspace-navigation.ts`.
- Correct implementation: server/session-aware permission surfaces and a matrix-tested resolver that only returns supported, useful next actions.
- Files affected: layouts, feature pages, resolver, query error classification.
- Tests required: role/capability/onboarding/suspension/feature matrix and direct forbidden routes.
- Final verification result: repository format/lint/typecheck, 40 web tests, 58 API tests, OpenAPI generation, and a Playwright smoke test pass; local DB drift check is blocked by unavailable PostgreSQL.

### 8. CI and browser determinism

- Severity: P0
- User impact: PR feedback is blocked at migration drift; local Windows Playwright leaves child processes and visual baselines are not Linux-owned.
- Root cause: migration/model mismatch, dev-server process tree behavior, and existing snapshot/config assumptions.
- Current implementation: `.github/workflows/ci.yml`, `apps/web/playwright.config.ts`, snapshot directories.
- Correct implementation: green Alembic/OpenAPI gates, owned server lifecycle, fixed locale/time/animations, and CI-compatible snapshots without weakened assertions.
- Files affected: CI workflow, Playwright config/scripts/snapshots.
- Tests required: clean checkout CI and complete E2E exit.
- Final verification result: Pending.
