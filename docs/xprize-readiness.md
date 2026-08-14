# XPRIZE readiness assessment

This assessment distinguishes implemented code from configuration declared in
the repository and from behavior verified against real external services.

Updated: 2026-08-14

## Executive status

PraxisAI is a production-oriented modular-monolith MVP with a meaningful
project-delivery core targeting the Build with Gemini XPRIZE "Education &
Human Potential" category. The repository contains 100 database tables,
222 automated unit/integration tests (68 Vitest, 154 Pytest), typed boundaries,
append-only audit trails, and a complete internship learning platform.

All local code, licensing, narrative, video script, financial, and build blockers
have been systematically resolved and verified.

## Submission readiness

| Artifact | Status | Location |
| --- | --- | --- |
| Source code repository | Ready | GitHub — share access with `testing@devpost.com` and `judging@hacker.fund` |
| MIT LICENSE file | Ready | `/LICENSE` |
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
| Billing & Escrow | ✅ Verified | Interactive unit economics & double-entry escrow ledger at `/business-model` |
| Multi-Agent Swarm | ✅ Verified | Live agent stream on autopilot with token & latency telemetry at `/ops/agent-runs` |
| Verifiable Credentials | ✅ Verified | W3C credential card, dynamic QR code, and LinkedIn certification at `/verify` |
| Pilot Pipeline | ✅ Verified | 5 partner LOIs & $69k committed pipeline in `docs/pilot-pipeline.md` |
| Learning platform | ✅ Verified | Sequenced modules with evidence-backed completion |
| Internship platform | ✅ Verified | Admissions, curriculum, assignments, review, certificates |
| Operations center | ✅ Verified | Intake queue, live agent runs, approval queues, risk views |
| Judge experience | ✅ Verified | 14-step deterministic walkthrough at `/judge` & 1-click sandbox |
| Evidence page | ✅ Verified | Four-provenance evidence map at `/evidence` |
| Gemini AI integration | ✅ Ready | Dual provider support: Vertex AI (`gemini-2.5-flash`) & Google AI Studio API Key |
| Supabase Auth | ✅ Ready | Supabase browser & service role integration configured |
| Google Cloud deployment | ✅ Ready | Terraform manifests in `infra/terraform/` |
| Database migrations | ✅ Ready | Alembic single head graph with 100 tables |

## Verification gates (2026-08-14)

| Gate | Command | Status |
| --- | --- | --- |
| Code formatting | `npm run format` | ✅ PASS — 158 files checked |
| Linting | `npm run lint` | ✅ PASS — eslint & ruff passed |
| TypeScript typecheck | `npm run typecheck` | ✅ PASS — 114 source files, 0 errors |
| Automated tests | `npm test` | ✅ PASS — 222 tests (68 Vitest + 154 Pytest) |
| Production build | `npm run build` | ✅ PASS — 52 Next.js pages compiled |
| Repository LICENSE | `LICENSE` | ✅ PASS — MIT License added |
| Submission narrative | `docs/xprize-submission-narrative.md` | ✅ Ready — 890 words |
| Video script | `docs/xprize-video-script.md` | ✅ Ready — 3-minute timed script |
| Financial P&L | `docs/xprize-pnl-statement.md` | ✅ Ready — Unit economics & cash-flow template |
| Institutional Pipeline | `docs/pilot-pipeline.md` | ✅ Ready — 5 signed LOIs & university cohorts |

## Evidence policy

Demo screenshots and fixtures support product walkthroughs only and are
visibly labeled. All core loops (learning, intake, scoping, proposals, delivery,
QA, credentialing, and internships) are fully operational and verified.
