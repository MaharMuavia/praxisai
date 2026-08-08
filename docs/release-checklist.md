# PraxisAI XPRIZE release checklist

This checklist is evidence-based. `passed` means the command ran against the
current working tree; `blocked` means an external dependency or authority was
unavailable; `unverified` means no evidence was produced.

## Current release record

- Release branch: `release/xprize-2026`
- Current HEAD: `6cab5d40444c5f4a8f01494f26e042ecd91cfe39` (working tree dirty)
- Migration head: `c2d3e4f5a6b7`
- Pull request, merge, tag, image digest: unverified
- License: blocked; no owner-approved `LICENSE` exists

## Local verification — 2026-08-08

- API tests: passed, 87 tests
- Web tests: passed, 50 tests
- Ruff format/check: passed
- Strict mypy: passed
- TypeScript: passed
- Web ESLint: passed with no warnings
- API client generation/build: passed
- `npm audit --audit-level=high`: passed, 0 vulnerabilities
- Terraform `fmt -check`, backend-disabled `init`, and `validate`: passed
- Staging-semantics web build with non-secret Firebase placeholders: passed
- Default web build: blocked by absent Firebase public build variables
- Playwright E2E: blocked before assertions; Chromium executable missing
- Python dependency audit: unverified; PyPI access blocked
- PostgreSQL migration/vertical-slice test: unverified; configured database unavailable
- Docker image build/scan and hosted smoke tests: unverified

## Release decision

The branch is not release-ready. Local hardening covers proxy trust boundaries,
transition idempotency, upload limits, task-envelope shape, and selected
Terraform/IAM configuration. CRM/admissions, complete outbox processing,
provider-backed staging evidence, PostgreSQL integration, E2E browser coverage,
and XPRIZE proof remain unresolved. See
[`docs/release-readiness.md`](release-readiness.md) and
[`docs/staging-smoke-report.md`](staging-smoke-report.md).
