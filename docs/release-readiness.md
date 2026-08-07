# XPRIZE release readiness

This document records release gates for `release/xprize-2026`. A gate is only
`passed` when it has been executed against the current working tree. External
systems and evidence are not inferred from source code.

## Passed locally on the current working tree

- npm dependency audit at high severity: 0 vulnerabilities.
- Python dependency audit: no known vulnerabilities.
- API test suite: 85 tests passed.
- Web unit suite: 46 tests passed.
- Strict TypeScript, strict mypy, ESLint, Ruff, formatting, and API client build.
- Application resources are now addressed by application ID plus authenticated
  applicant ID, with explicit frontend selection for multiple applications.
- Internship queries now resolve an explicit enrollment context and constrain
  curriculum, assignments, and progress to the selected cohort track.
- Completion decisions now require idempotency, expected version, row locking,
  decision validation, a rejection reason, and target-student audit data.
- Production upload completion now quarantines objects and emits a
  `MalwareScanRequested` outbox event; the worker has a bounded ClamAV path.

## Failed

- Full Grype scans fail on high/critical findings in the official Python and
  Node Debian 13 base images. Fixable JavaScript runtime findings were removed
  with npm from the web runtime; its actionable-only scan passes. Vendor-unfixed
  Debian and Python findings remain and have no approved exception.

## Blocked

- Terraform checks: blocked because Terraform is not installed locally.
- Web production build: blocked because Firebase public build variables are not
  available in this workspace.
- Public license: an owner-approved license has not been selected.
- Release PR, merge, tag, and repository metadata: blocked while security CI is
  known to fail and while the requested implementation phases remain incomplete.
- Staging/production deployment, immutable registry digests, Cloud Run revisions,
  real Gemini/KMS/email/telemetry smoke evidence, and production URL: no cloud
  project credentials or approved environments are available in this workspace.
- Arms-length customer, revenue, payout, consent, corporate-ID, and competition
  evidence: must come from real authorized records and cannot be fabricated.

## Unverified or incomplete

- PostgreSQL migration upgrade/check and a PostgreSQL integration test for the
  complete client-to-paid-student lifecycle.
- The shared typed Gemini runtime, expanded persisted run schema, typed action
  registry, 30-case evaluation harness, and real-Gemini staging smoke test.
- Judge-flow feature flags and route ownership refactor requested in phases 1-4.
- Production-backed versioned evidence metrics and privacy-safe submission exports.
- Separate staging/production Terraform state, deployment promotion, rollback,
  alerting, backup/restore drill, and protected production workflow.
- XPRIZE submission narrative, approved media, consented customer evidence, and
  exact deployed commit/image digest references.

No release merge or production promotion is authorized while any failed gate
above remains unresolved or lacks a documented, owner-approved, time-bounded
exception.
