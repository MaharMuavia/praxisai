# PraxisAI XPRIZE release checklist

This checklist is evidence-based. `passed` means the command was run against
the current working tree; `blocked` means an external dependency or required
release authority is unavailable; `unverified` means no evidence was produced.

## Current release record

- Release branch: `release/xprize-2026`
- Source branch: `agent/internship-platform-completion`
- Source SHA: `7d48e4f1e050551c0f7135282874dda91101d463`
- Current working-tree tip: `f8b40967bfc03c3e655c3ab5617a076a7411e614`
- Target branch: `main`
- Target SHA at inspection: `d8e4156370418c7c07025c7866fa55e73fdf3a94`
- Migration head after this change: `f6b2c3d4e5f6`
- Current working-tree changed paths: 21, including untracked release changes
- Current CI status: unverified
- Pull request to `main`: unverified; no PR was opened by this workspace

## Repository controls

- Security policy: passed
- Contribution guide: passed
- Code owners: passed (`.github/CODEOWNERS`)
- Pull request template: passed
- Changelog: passed
- Release checklist: passed (this file)
- License: blocked; no owner-approved `LICENSE` exists

## Local verification

- API tests: passed, 85 tests
- Web tests: passed, 46 tests across 20 files
- Ruff: passed
- Strict mypy: passed
- Web TypeScript: passed
- Web ESLint: passed with 4 pre-existing warnings
- Web Prettier: passed
- API client build: passed
- npm audit at high severity: passed, 0 vulnerabilities
- Python dependency audit: passed, no known vulnerabilities
- Terraform checks: blocked; Terraform is not installed in the workspace
- Web production build: blocked; Firebase public build variables are unavailable
- Local test/demo optimized web build: passed with `NEXT_PUBLIC_APP_ENV=test`
  and `NEXT_PUBLIC_DEMO_MODE=true`
- PostgreSQL migration upgrade/check: unverified; no PostgreSQL service was available
- Docker image builds/scans: unverified; no release images or digests were produced

## Release decision

The branch is not release-ready. Application scoping, enrollment context,
completion concurrency, submission draft concurrency, and quarantine scan
workflow corrections are implemented and tested. The broader lifecycle,
credential integration, production deployment, customer evidence, and XPRIZE
proof requirements remain blocked or unverified as recorded in
`docs/release-readiness.md`.
