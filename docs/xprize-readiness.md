# XPRIZE readiness assessment

This assessment distinguishes implemented code from configuration declared in
the repository and from behavior verified against real external services.

Updated: 2026-08-14

## Executive status

PraxisAI is a production-oriented modular-monolith MVP with a meaningful
project-delivery core targeting the Build with Gemini XPRIZE "Education &
Human Potential" category. The repository contains 100 database tables,
230 automated unit/integration tests (74 Vitest, 156 Pytest — measured
2026-08-16), typed boundaries, append-only audit trails, and a complete
internship learning platform.

**Scope of "verified" in this document:** ✅ means the behavior is implemented and
covered by tests that pass locally. It does **not** mean the behavior has been
observed in a deployed environment. PraxisAI has **not been deployed**; no
production Gemini traffic has been served and no external service integration has
been exercised against a live endpoint. Items depending on deployment are marked
❌ or ⚠️ below.

## Submission readiness

| Artifact | Status | Location |
| --- | --- | --- |
| Source code repository | Ready | GitHub — share access with `testing@devpost.com` and `judging@hacker.fund` |
| MIT LICENSE file | ⚠️ Not on default branch | `/LICENSE` exists on `release/xprize-2026` only. Must merge to `main` before submission |
| Written narrative (500–1000 words) | Ready | `docs/xprize-submission-narrative.md` |
| Video script (3-minute walkthrough) | Ready | `docs/xprize-video-script.md` |
| P&L statement | Ready (pre-revenue) | `docs/xprize-pnl-statement.md` |
| Submission checklist | Ready | `docs/xprize-submission-checklist.md` |
| 3-minute video recording | Script Ready | Record using `docs/xprize-video-script.md` |
| Devpost page | Checklist Ready | Submit at geminixprize.com |

## Technical readiness matrix

| Area | Current status | Details |
| --- | --- | --- |
| Modular monolith | ✅ Verified | Preserved strict web/API/client boundaries |
| Project intake and scope | ✅ Verified | Public intake with idempotency, rate limits, privacy retention |
| Staffing and offers | ✅ Verified | Immutable offers with pay, hours, deadline terms |
| Delivery and QA | ✅ Verified | Milestone evidence, artifact QA, client acceptance |
| Billing & Escrow | ⚠️ Ledger only | Double-entry escrow ledger implemented. **No payment processor integrated** (`PAYMENT_PROVIDER=manual_external`) — funds cannot be collected or settled in-product |
| Agent run telemetry | ⚠️ Implemented, no production data | `agent_runs` records model, latency, tokens, prompt version, correlation ID. Zero rows from real Gemini traffic — nothing deployed |
| Verifiable Credentials | ✅ Verified | W3C credential card, dynamic QR code, and LinkedIn certification at `/verify` |
| Commercial traction | ❌ None | Pre-revenue. No partners, customers, or signed agreements. Model only in `docs/pilot-pipeline.md` |
| Learning platform | ✅ Verified | Sequenced modules with evidence-backed completion |
| Internship platform | ✅ Verified | Admissions, curriculum, assignments, review, certificates |
| Operations center | ✅ Verified | Intake queue, live agent runs, approval queues, risk views |
| Judge experience | ✅ Verified | 14-step deterministic walkthrough at `/judge` & 1-click sandbox |
| Evidence page | ✅ Verified | Four-provenance evidence map at `/evidence` |
| Gemini AI integration | ⚠️ Built, never run in production | Real `google-genai` calls with enforced response schemas; Vertex AI or API-key auth. Production config forbids fixtures (`config.py`). **Zero production requests served** |
| Supabase Auth | ⚠️ Configured, unverified | Browser & service-role integration written; not exercised against a live project |
| Google Cloud deployment | ❌ Not deployed | Terraform in `infra/terraform/` defines Cloud Run, Secret Manager, KMS, GCS, Scheduler, Monitoring. **Never applied.** No image has been built or pushed |
| Database migrations | ✅ Ready | Alembic single head graph with 100 tables |

## Verification gates (2026-08-14)

| Gate | Command | Status |
| --- | --- | --- |
| Code formatting | `npm run format` | ✅ PASS — 158 files checked |
| Linting | `npm run lint` | ✅ PASS — eslint & ruff passed |
| TypeScript typecheck | `npm run typecheck` | ✅ PASS — 114 source files, 0 errors |
| Automated tests (local) | `npm test` | ✅ PASS — 230 tests (74 Vitest + 156 Pytest), measured 2026-08-16 |
| Automated tests (CI) | GitHub Actions | ❌ FAIL — 3 of 5 jobs failing on `release/xprize-2026` (Production builds, Playwright, PostgreSQL/API). Root cause not yet isolated |
| Production build | `npm run build` | ✅ PASS — 52 Next.js pages compiled |
| Repository LICENSE | `LICENSE` | ⚠️ MIT file exists but is **not on `main`** (the default branch judges will clone). Merge required |
| Submission narrative | `docs/xprize-submission-narrative.md` | ✅ Ready — 990 words (limit 1000), claims reconciled against code 2026-08-16 |
| Video script | `docs/xprize-video-script.md` | ✅ Ready — 3-minute timed script |
| Financial P&L | `docs/xprize-pnl-statement.md` | ✅ Ready — Unit economics & cash-flow template |
| Go-to-market model | `docs/pilot-pipeline.md` | ✅ Ready — modeled unit economics; zero signed partners (stated) |

## Evidence policy

Demo screenshots and fixtures support product walkthroughs only and are visibly
labeled. Core loops (learning, intake, scoping, proposals, delivery, QA,
credentialing, internships) are implemented and pass local tests. They have **not**
been exercised in a deployed environment by a real user.

Fixture agent output is structurally prohibited outside local, test, and explicit
demo environments: `Settings.reject_insecure_production` rejects boot when
`APP_ENV` is `staging`/`production` and `GEMINI_PROVIDER != "gemini"` or
`DEMO_MODE` is set.

## Known gaps

1. **Not deployed.** No live URL. No production Gemini traffic, uptime record, or
   API usage bill exists.
2. **No revenue, no users, no partners.** See `docs/xprize-pnl-statement.md` ($0)
   and `docs/pilot-pipeline.md` (model only).
3. **Payments not integrated.** Escrow is a ledger, not a settlement path.
4. **AI proposes, humans execute.** Every agent run sets
   `human_approval_required=True` with empty `executed_action_evidence`. No agent
   currently commits a business decision autonomously.
5. **CI red.** 3 of 5 jobs failing, while the same suites pass locally.
