# PraxisAI XPRIZE release checklist

Use [`release-readiness.md`](release-readiness.md) as the single evidence
record. This checklist contains release metadata and the commands that must be
rerun from a clean checkout before merge.

## Current release record — 2026-08-11

- Branch: `release/xprize-2026`
- HEAD at inspection: `ad7b8fa295a7a8e7aa49e5f64d77d24b366fa4fb`
- Worktree: dirty from uncommitted remediation changes
- Repository Alembic head: `d5e6f7a8b9c0` (single head)
- Configured database revision: `c8f1a2d4e609` (migration required)
- Verified pre-migration backup: `praxisai-pre-c3d4e5f6a7b8-20260811-235304.dump`
  (502,338 bytes; SHA-256
  `37e3f745f4d10a99c5ac570d0ec4f4e1624f40bd3b1203db0233f0fcd41995ee`)
- Local API image: `sha256:a701772263145cd107c983d22f86991c1dfd607f10c33c311cdf2756b6fde0a7`
- Local web image: `sha256:8d4650b8700ae390f3c091d0fc048498171bd1d88977f8ca6478b227353b07cd`
- Local Grype gate: PASS at high with Grype 0.116.1 and `.grype.yaml`
- Current-tree PR, merge, tag, and image digest: NOT RUN
- License: MIT (owner-approved)

## Required clean-checkout commands

```text
npm ci
uv sync --project apps/api --frozen
npm run format
npm run lint
npm run typecheck
npm test
npm run db:verify-fresh
npm run db:current
npm run db:check
npm run test:e2e
npm run build
npm run eval:agents
npm audit --audit-level=high
uv run --project apps/api pip-audit
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform init -backend=false -input=false
terraform -chdir=infra/terraform validate
```

The clean CI build must upload its exact image digests, manifests, extracted
provenance and SBOM attestations, and both pinned Grype 0.116.1 JSON reports.
For promotion, run the protected manual **Release container images** workflow.
It must build both images only once, scan the returned Artifact Registry digests
with `.grype.yaml` at the high threshold, and upload a checksummed evidence
artifact containing `terraform-images.tfvars`. A local rebuild is not release
evidence and must never replace either digest.

The web build requires valid non-secret `NEXT_PUBLIC_SUPABASE_URL` and
`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` values. If port 3000 is occupied, set
`PLAYWRIGHT_PORT` to a free port before the E2E command. System Chrome may be
selected with `PLAYWRIGHT_USE_SYSTEM_CHROME=true`.

## Operator-only database step

Do not migrate a shared database as part of an unaudited local test run. The
pre-migration PostgreSQL 17 backup has been created, its 1,105-entry TOC parsed,
and its contents fully decoded without error. After an authorized operator
confirms the maintenance window and explicitly authorizes the remote DDL:

- The configured upgrade spans nine revisions from `c8f1a2d4e609` to
  `c3d4e5f6a7b8`.
- The upgrade does not drop existing rows, tables, or columns. It creates the
  public-intake and internship structures, replaces three uniqueness
  constraints/indexes on the newly introduced internship tables, and adds
  columns/indexes to `project_transitions`, `outbox_events`, and `agent_runs`.
- These DDL operations can take PostgreSQL locks. Schedule a maintenance window
  sized for the existing transition, outbox, and agent-run tables.
- Do not use Alembic downgrade as the production rollback after new writes:
  the downgrade path removes the new tables and columns. Restore the verified
  backup or roll forward with a reviewed corrective migration.

```text
npm run db:migrate
npm run db:current
npm run db:check
```

Every command must be recorded as PASS, FAIL, BLOCKED, or NOT RUN in
[`release-readiness.md`](release-readiness.md). No release merge or promotion
is authorized while required gates are unresolved.
