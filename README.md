# PraxisAI

**An AI-operated apprenticeship studio** — connecting practical learning directly to paid, supervised project work. Students build employer-relevant skills, respond to real project briefs with professional proposals, and carry selected work through verified delivery to a cryptographically signed credential.

> **Build with Gemini XPRIZE submission — Category: Education & Human Potential**

## Honest status (read this first)

PraxisAI is a **production-oriented MVP, pre-revenue and pilot-stage**. We do not invent users, revenue, or partnerships.

| | Status |
| --- | --- |
| Core product loop (learn → propose → deliver → QA → credential) | ✅ Implemented, 230 tests pass locally |
| Gemini agent workflows (scoping, planning, QA, multimodal QA) | ✅ Real `google-genai` calls with enforced schemas |
| Revenue / paying customers / signed partners | ❌ None — $0 ([P&L](docs/xprize-pnl-statement.md)) |
| Payment processor | ❌ Not integrated (`PAYMENT_PROVIDER=manual_external`) |
| Cloud deployment | ❌ Defined in Terraform, **not yet applied** — no live URL |
| Autonomous AI execution | ❌ Agents propose; humans approve every consequential decision |

Where fixture or demo data appears in the app, it is visibly labeled **Demo data**.

## How Gemini is used (AI-Native Operations)

A single typed adapter ([`apps/api/app/agents/provider.py`](apps/api/app/agents/provider.py)) drives four production-designed workflows, each with **enforced structured output** (`response_schema`) so malformed model output fails closed instead of entering the database:

| Workflow | What Gemini does | Prompt |
| --- | --- | --- |
| **Scoping** | Turns a raw client brief into deliverables, acceptance criteria, effort, risks | [`prompts.py`](apps/api/app/agents/prompts.py) |
| **Planning** | Decomposes an accepted scope into milestones/tasks covering every criterion | `prompts.py` |
| **QA review** | Assesses immutable artifact evidence against the accepted scope | `prompts.py` |
| **Multimodal QA** | Analyzes screenshots/PDFs/diagrams via `Part.from_bytes` against a rubric | `prompts.py` |

Each run is recorded append-only in `agent_runs` (model, prompt version, latency, token usage, retry count, correlation ID, input-snapshot hash) — visible in the operations center. Prompts are versioned and centralized, treat every brief as untrusted data, and the adapter applies bounded retries with backoff and a 30s timeout. Production configuration **refuses to boot** with fixture AI or demo mode enabled ([`config.py`](apps/api/app/config.py), `reject_insecure_production`).

**Authority boundary:** agents only propose. Every run stores `human_approval_required=true` with empty `executed_action_evidence`; humans retain authority over money, contracts, admissions, credentials, and release.

## Google Cloud usage

Used in code: **Vertex AI** (Gemini), **Cloud Storage** (artifacts). Defined in Terraform under [`infra/terraform/`](infra/terraform/) but **not yet deployed**: Cloud Run (api/web/worker), Secret Manager, KMS, Cloud Scheduler, Cloud Monitoring alerts, Logging sink, Workload Identity Federation, Artifact Registry.

## Architecture

Modular monolith with strict boundaries:

- **Web** — Next.js app (`apps/web/`)
- **API** — FastAPI transactional service (`apps/api/`), 100 PostgreSQL tables, single Alembic head
- **Worker** — outbox consumer for async analytics and notifications
- **Client** — generated TypeScript API client (`packages/api-client/`)

PostgreSQL is authoritative. Business state transitions live in domain services that enforce workflow guards; agents never mutate high-risk state.

## Local setup

Requirements: Node.js 22+, Python 3.13+, `uv`, Docker, Git.

```bash
cp .env.example .env          # replace the local session secrets
docker compose up -d postgres
npm run setup                 # install, migrate, generate API client
npm run seed:demo             # deterministic demo tenant
npm run worker:once           # deliver seeded notifications
npm run dev                   # http://localhost:3000
```

On Windows use `npm.cmd` if PowerShell blocks `npm.ps1`. The Makefile mirrors the npm commands.

## Judge / evaluator access

The app is not deployed, so evaluation is local. After `npm run seed:demo`:

1. Open **`http://localhost:3000/login`** and select a seeded demo user (no password — local demo role-switch):
   - **Amina Noor** (`amina@student.demo`) — student: curriculum, proposal builder, active delivery
   - **Maya Chen** (`maya@northstar.demo`) — employer: briefs, proposal review
   - **Sara Malik** — coordinator: operations queue, agent evidence
2. Visit **`/judge`** for an interactive deterministic walkthrough of the agent contract and boundaries.
3. Visit **`/evidence`** for a provenance map of mock vs. fixture vs. local vs. external data.
4. Follow [`docs/demo-script.md`](docs/demo-script.md) for the full guided path.

## Submission documents

- [Narrative](docs/xprize-submission-narrative.md) · [Video script](docs/xprize-video-script.md) · [P&L](docs/xprize-pnl-statement.md)
- [Go-to-market model](docs/pilot-pipeline.md) · [Readiness assessment](docs/xprize-readiness.md) · [Checklist](docs/xprize-submission-checklist.md)
- [Architecture](docs/architecture.md) · [Security & privacy](docs/security-and-privacy.md) · [Database schema](docs/database-schema.md) · [Configuration & secrets](docs/configuration-and-secrets.md)

## Safety defaults

- Fixture agents and local role switching run only in local/test or explicit demo mode; production forbids them.
- No payment processor is integrated. Coordinators may record independently verified external funding evidence; this does not initiate settlement.
- Production credential issuance requires KMS; local credentials use a disposable gitignored key and are marked demo.
- Credential revocation is append-only; public verification checks the original signature plus revocation history.
- University metrics require an active agreement and consented enrollment; cohorts below the configured minimum are suppressed, including in exports.

## License

MIT — see [`LICENSE`](LICENSE).
