# PraxisAI release readiness

This file is the release-readiness source of truth for `release/xprize-2026`.
It records evidence from the current working tree. Local tests do not prove
that a hosted service or external provider works.

## Verdict: NOT READY

The current source passes its local application gates. Release is still
blocked because the configured Supabase database is behind the repository
Alembic head, the final infrastructure and container artifacts have not been
verified from a clean hosted run, external-provider smoke evidence is missing,
and the repository has not been verified in a clean hosted run.

## Evidence — 2026-08-12

| Status  | Gate                           | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PASS    | Formatting and lint            | Web Prettier and ESLint passed. API Ruff reported `154 files already formatted` and `All checks passed!`. The single combined command could not be repeated after the desktop approval quota was exhausted; its components passed independently.                                                                                                                                                                                                                           |
| PASS    | Type checking                  | The generated API client built, web `tsc --noEmit` passed, and strict mypy reported no issues in 112 Python source files.                                                                                                                                                                                                                                                                                                                                                  |
| PASS    | Automated tests                | Vitest passed 61 tests across 24 files. Pytest passed all 146 tests under Python 3.13.14. Its only warning comes from the pinned `google-genai` dependency.                                                                                                                                                                                                                                                                                                                |
| PASS    | Browser E2E                    | Playwright passed all 79 tests with system Chrome on the isolated port 3107.                                                                                                                                                                                                                                                                                                                                                                                               |
| PASS    | Production web build           | `npm run build` compiled successfully and generated all 52 application pages using non-secret test values for the required public Supabase build variables. Missing production variables still fail closed.                                                                                                                                                                                                                                                                |
| PASS    | Generated API contract         | `npm run openapi` regenerated `openapi.json` and the strict TypeScript client successfully. Removed Cloud Tasks routes are absent.                                                                                                                                                                                                                                                                                                                                         |
| PASS    | Alembic graph                  | `alembic heads` reports one repository head: `c3d4e5f6a7b8`. The migration-graph regression test passes.                                                                                                                                                                                                                                                                                                                                                                   |
| FAIL    | Configured database revision   | The last successful remote check on 2026-08-11 reported `c8f1a2d4e609`, behind `c3d4e5f6a7b8`. A read-only recheck on 2026-08-12 was blocked by sandbox network permissions; no migration was attempted. The verified pre-migration backup is `praxisai-pre-c3d4e5f6a7b8-20260811-235304.dump` (502,338 bytes; SHA-256 `37e3f745f4d10a99c5ac570d0ec4f4e1624f40bd3b1203db0233f0fcd41995ee`; 1,105 TOC entries). Shared remote DDL requires explicit operator authorization. |
| PASS    | Fresh PostgreSQL migration     | On 2026-08-11, `npm run db:verify-fresh` upgraded an isolated PostgreSQL 16 schema through the complete graph to `c3d4e5f6a7b8` and dropped the probe schema. Docker was unavailable for a repeat run on 2026-08-12. No migration file changed after that successful probe.                                                                                                                                                                                                |
| PASS    | Deterministic AI evaluation    | `npm run eval:agents` passed all 32 fixture cases, including prompt-injection containment, stale-output rejection, cycle rejection, unsupported-action rejection, schema validity, and policy expectations. Live Gemini/Vertex evaluation remains unrun.                                                                                                                                                                                                                   |
| PASS    | Dependency audits              | `npm audit --audit-level=high` found 0 vulnerabilities. `pip-audit` found no known vulnerabilities in the locked API environment.                                                                                                                                                                                                                                                                                                                                          |
| PARTIAL | Secret scan                    | The last pinned Gitleaks run reported no committed-history leaks and the narrow fixture allowlist remains regression-tested. The current uncommitted tree still requires a clean hosted CI scan.                                                                                                                                                                                                                                                                           |
| NOT RUN | Current container images       | Earlier local image digests predate the latest worker, upload, and infrastructure fixes and are not release evidence. Docker was unavailable on 2026-08-12. The protected release workflow must build, attest, scan, and publish the current commit once.                                                                                                                                                                                                                  |
| PARTIAL | Terraform static checks        | Both Terraform stacks passed `fmt`, backend-disabled `init`, and `validate` before the final narrow lifecycle/filter hardening. After those edits, 16 focused configuration/security contract tests passed. A final Terraform invocation was blocked by the desktop approval quota, so `fmt -check` and `validate` must be repeated before planning. No infrastructure was applied.                                                                                        |
| NOT RUN | Clean CI and release artifacts | The remediation is uncommitted. No clean-checkout CI result, protected release run, immutable current image digest, or checksummed current evidence artifact exists.                                                                                                                                                                                                                                                                                                       |
| BLOCKED | Hosted and provider evidence   | No current staging proof exists for Supabase Auth/PKCE, database readiness, private Storage, private ClamAV reachability, scheduled worker execution, Vertex/Gemini, KMS signing and rotated-key verification, alert delivery, backup restore, rollback, or the public credential and funding workflows.                                                                                                                                                                   |
| PASS    | Repository license             | An owner-approved `LICENSE` file exists (MIT).                                                                                                                                                                                                                                                                                                                                                                                             |

## Production hardening completed in this working tree

- Supabase is the hosted PostgreSQL, Auth, and private Storage platform. Identity
  linking is subject-first, confirmation uses a PKCE callback, and hosted URLs
  must use HTTPS.
- Uploads are capped at 30 MiB, streamed through the web proxy, deterministically
  type/archive-validated before ClamAV, cleaned up on rejection or mismatch, and
  retained through bounded, retryable policies.
- Notifications, malware scans, and retention run in a scheduled Cloud Run Job.
  Outbox claims reject concurrent execution and recover stale worker claims.
- Hosted secrets use pinned numeric versions. Session verification supports a
  staged fallback key, migration credentials are absent from runtime identities,
  KMS uses an explicit key version, and protected secret/log resources resist
  accidental destruction.
- The worker uses Direct VPC egress to an RFC1918 ClamAV endpoint. Cloud Run
  readiness checks the exact Alembic head, rate limits use verified principals,
  and service/worker alerts have an operator notification channel.
- CI and the protected release workflow use Workload Identity Federation,
  digest-pinned images, SBOM/provenance attestations, exact-digest scans, and
  checksummed release evidence. The workflow still needs a real staging run.

## Required operator actions

1. Explicitly authorize the maintenance window and `npm run db:migrate`, then
   require `npm run db:current` and `npm run db:check` to report
   `c3d4e5f6a7b8`.
2. Rerun Terraform `fmt -check` and `validate`, review a saved remote-state
   staging plan, and apply only with explicit operator approval.
3. Configure protected GitHub Environments and Google Workload Identity, run
   clean CI, then execute the manual release workflow and retain its checksummed
   digest, attestation, SBOM, and scan artifact.
4. Deploy staging and capture the hosted/provider evidence listed above,
   including a restore/rollback drill and alert delivery.

No release merge, tag, infrastructure apply, or production promotion is
authorized while a FAIL or BLOCKED gate remains unresolved or has a documented,
owner-approved exception.
