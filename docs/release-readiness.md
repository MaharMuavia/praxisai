# XPRIZE release readiness

This document records release gates for `release/xprize-2026`. A gate is only
`passed` when it has been executed against the current working tree. External
systems and evidence are not inferred from source code.

## Passed locally

- npm dependency audit at high severity: no known vulnerabilities.
- Python dependency audit: no known vulnerabilities.
- Full Git-history secret scan: 28 commits scanned, no leaks found.
- API test suite: 79 tests passed.
- Web unit suite: 46 tests passed.
- Playwright functional and reviewed visual suite: 79 tests passed using local
  system Chrome because the pinned Chromium CDN download was unavailable.
- Strict TypeScript, strict mypy, ESLint, Ruff, formatting, OpenAPI drift,
  Alembic upgrade/check, Terraform formatting/init/validation, API image build,
  and web image build.

## Failed

- Full Grype scans fail on high/critical findings in the official Python and
  Node Debian 13 base images. Fixable JavaScript runtime findings were removed
  with npm from the web runtime; its actionable-only scan passes. Vendor-unfixed
  Debian and Python findings remain and have no approved exception.

## Blocked

- Public license: an owner-approved license has not been selected.
- Release PR, merge, tag, and repository metadata: blocked while security CI is
  known to fail and while the requested implementation phases remain incomplete.
- Staging/production deployment, immutable registry digests, Cloud Run revisions,
  real Gemini/KMS/email/telemetry smoke evidence, and production URL: no cloud
  project credentials or approved environments are available in this workspace.
- Arms-length customer, revenue, payout, consent, corporate-ID, and competition
  evidence: must come from real authorized records and cannot be fabricated.

## Unverified or incomplete

- A PostgreSQL integration test for the complete client-to-paid-student lifecycle.
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
