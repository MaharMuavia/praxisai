# XPRIZE release readiness

This is the release record for the current working tree on `release/xprize-2026`.
It separates repository evidence from staging and production evidence. Source
code, Terraform declarations, and unit tests do not prove that an external
provider or hosted revision is working.

## Current status — 2026-08-08

The branch is not release-ready. The release-blocking code paths below were
hardened locally, but there is no staging or production evidence in this
workspace. The broader CRM/admissions lifecycle, complete hosted outbox
processing, real-provider smoke tests, and competition evidence remain
incomplete or unverified.

## Implemented and locally verified

- Same-origin API proxy now strips client-supplied forwarding, service-auth,
  and authorization headers; upstream `Set-Cookie` values are preserved
  individually. Next 16 uses `proxy.ts` for the request boundary.
- Project transition idempotency is tenant/resource scoped, hashes the
  request payload, and tests replay, payload mismatch, cross-resource, and
  cross-tenant cases. A migration adds the persisted contract fields.
- Cloud Tasks payloads contain only event metadata and correlation identity;
  the hosted task route verifies Cloud Tasks identity when configured and
  currently dispatches only notification events.
- Upload streaming enforces the declared byte limit before accepting an
  oversized object and removes the partial local object on rejection.
- Terraform validates with backend initialization disabled. API ingress is
  compatible with the same-origin proxy, invocation remains IAM-restricted,
  and the logging sink has an object-creator grant.
- `npm audit --audit-level=high`: 0 vulnerabilities.
- 87 API tests and 50 web tests passed.
- Ruff format/check, strict mypy, TypeScript, ESLint, API-client generation,
  and the hosted-semantics web build passed locally.

## Failed or blocked gates

- Default web build fails closed because the required Firebase public build
  variables are not present. A staging-semantics build with non-secret
  placeholders passed; that is not deployment evidence.
- Playwright E2E could not start its 79 tests because the required Chromium
  executable is not installed. No E2E assertion result is being claimed.
- PostgreSQL connectivity and `db:check` are blocked by unavailable/unresolvable
  Supabase configuration. No PostgreSQL migration upgrade or vertical-slice
  integration run was completed. SQLite validation reaches a pre-existing
  unsupported direct-constraint-alter migration and is not a substitute.
- `pip-audit` is unverified because the environment could not reach PyPI; no
  Python dependency-audit pass is claimed.

## Not yet proven or not implemented

- Hosted Firebase auth, Vertex/Gemini, KMS signing, email, ClamAV, telemetry,
  Cloud Tasks OIDC, Cloud Run routing, alerts, backups, rollback, and managed
  database behavior.
- Full outbox handler registry for malware, analytics, credential, and
  notification workflows. The current task endpoint intentionally returns a
  retryable error for unregistered event types.
- CRM/lead intake, admissions/readiness, complete client-to-paid-student
  vertical slice, shared typed agent runtime/action registry, 30-case AI
  evaluation, and source-backed evidence-center exports.
- Production customer, revenue, payout, consent, identity, or competition
  evidence. These must come from authorized source systems.
- Release PR, merge, tag, immutable image digests, approved license, and
  production promotion.

No release merge or production promotion is authorized while these gates are
unresolved or lack an owner-approved, time-bounded exception.
