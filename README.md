<div align="center">

# 🎓 PraxisAI

### An AI-operated apprenticeship studio — real preparation, paid projects, verified careers

Students deliver real, supervised software & data projects for companies and earn a
**cryptographically verifiable credential**. Google **Gemini** operates the core delivery
workflows — scoping, planning, and multimodal QA — under strict human authority.

<br>

![License](https://img.shields.io/badge/License-MIT-3da639?style=flat-square)
![Tests](https://img.shields.io/badge/tests-230%20passing-2ea043?style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js%2016-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini%202.5-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)

**🏆 Build with Gemini XPRIZE · Education & Human Potential**

</div>

---

## ✨ At a glance

<table>
<tr>
<td width="50%" valign="top">

### 🤖 AI-Native operations
Four Gemini workflows — scoping, planning, QA, and multimodal QA — with **enforced structured
output**. Every run is recorded append-only with full audit metadata.

</td>
<td width="50%" valign="top">

### 🛡️ Safety by design
Agents **propose**; humans approve every decision on money, access, and credentials. Malformed
AI output **fails closed** instead of entering the database.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🎓 Verified delivery
Completed work produces a **W3C Verifiable Credential** (Ed25519 / Cloud KMS) with append-only
revocation and public, checkable verification.

</td>
<td width="50%" valign="top">

### 🔍 Radically honest
Pre-revenue and pre-launch — **no invented users, revenue, or partners**. Every fact below is
verifiable in this repository.

</td>
</tr>
</table>

---

## 📊 Honest status

> PraxisAI is a **production-oriented MVP, pre-revenue and pilot-stage**. We do not invent users,
> revenue, or partnerships — everything here is verifiable in this repo.

**✅ Built &amp; verified**

| Capability | Status |
| --- | --- |
| Core product loop (learn → propose → deliver → QA → credential) | Implemented · **230 tests pass locally** |
| Gemini agent workflows (scoping, planning, QA, multimodal QA) | Real `google-genai` calls, enforced schemas · [live run evidence](docs/evidence/live-scoping-run.json) |
| Append-only audit trail, escrow ledger, signed credentials + revocation | Implemented &amp; tested |
| Google Cloud footprint (Cloud Run, KMS, Secret Manager, Storage, Scheduler, Monitoring) | Defined in Terraform |

**🟡 Next milestones** *(where we honestly are today)*

| Milestone | Today |
| --- | --- |
| Revenue &amp; customers | **Pre-revenue — $0**, no signed partners yet · [P&L](docs/xprize-pnl-statement.md) · [early feedback](docs/customer-evidence.md) |
| Payment processor | Not yet integrated (`PAYMENT_PROVIDER=manual_external`) |
| Cloud deployment | Defined in Terraform, **not yet applied** — no live URL |
| Autonomous execution | **By design**, agents propose and a human approves every consequential decision |

Where fixture or demo data appears in the app, it is always visibly labeled **Demo data**.

---

## 🤖 How Gemini operates the studio

A single typed adapter ([`apps/api/app/agents/provider.py`](apps/api/app/agents/provider.py))
drives four production-designed workflows, each with **enforced structured output**
(`response_schema`) so malformed model output fails closed instead of entering the database:

| Workflow | What Gemini does |
| --- | --- |
| **Scoping** | Turns a raw client brief into deliverables, acceptance criteria, effort, and risks |
| **Planning** | Decomposes an accepted scope into milestones/tasks covering every criterion |
| **QA review** | Assesses immutable artifact evidence against the accepted scope |
| **Multimodal QA** | Analyzes screenshots / PDFs / diagrams via `Part.from_bytes` against a rubric |

Each run is recorded append-only in `agent_runs` (model, prompt version, latency, token usage,
retry count, correlation ID, input-snapshot hash) — visible in the operations center. Prompts are
versioned and centralized, treat every brief as untrusted data, and the adapter applies bounded
retries with backoff and a 30s timeout. Production configuration **refuses to boot** with fixture
AI or demo mode enabled ([`config.py`](apps/api/app/config.py), `reject_insecure_production`).

> **Authority boundary:** agents only propose. Every run stores `human_approval_required=true`
> with empty `executed_action_evidence`; humans retain authority over money, contracts,
> admissions, credentials, and release.

**See it live yourself** — one real Gemini call, no deployment needed:

```bash
uv run --project apps/api python scripts/live_agent_demo.py
```

## ☁️ Google Cloud usage

Used in code: **Gemini** (`google-genai`, `gemini-2.5-flash`; Vertex AI supported), **Cloud KMS**
(credential signing), **Cloud Storage** (artifacts). Defined in Terraform under
[`infra/terraform/`](infra/terraform/) but not yet deployed: Cloud Run (api/web/worker), Secret
Manager, Cloud Scheduler, Cloud Monitoring, Logging, Workload Identity Federation, Artifact Registry.

## 🏗️ Architecture

Modular monolith with strict boundaries:

- **Web** — Next.js app (`apps/web/`)
- **API** — FastAPI transactional service (`apps/api/`), 100 PostgreSQL tables, single Alembic head
- **Worker** — outbox consumer for async analytics and notifications
- **Client** — generated TypeScript API client (`packages/api-client/`)

PostgreSQL is authoritative. Business state transitions live in domain services that enforce
workflow guards; agents never mutate high-risk state.

## 🚀 Local setup

Requirements: Node.js 22+, Python 3.13+, [`uv`](https://docs.astral.sh/uv/), Docker, Git.

```bash
cp .env.example .env          # replace the local session secrets
docker compose up -d postgres
npm run setup                 # install, migrate, generate API client
npm run seed:demo             # deterministic demo tenant
npm run worker:once           # deliver seeded notifications
npm run dev                   # http://localhost:3000
```

On Windows use `npm.cmd` if PowerShell blocks `npm.ps1`. The Makefile mirrors the npm commands.

## 🧑‍⚖️ Judge / evaluator access

The app is not deployed, so evaluation is local. After `npm run seed:demo`:

1. Open **`http://localhost:3000/login`** and select a seeded demo user (no password — local demo role-switch):
   - **Amina Noor** (`amina@student.demo`) — student: curriculum, proposal builder, active delivery
   - **Maya Chen** (`maya@northstar.demo`) — employer: briefs, proposal review
   - **Sara Malik** — coordinator: operations queue, agent evidence
2. Visit **`/judge`** for an interactive walkthrough of the agent contract and boundaries.
3. Visit **`/evidence`** for a provenance map of mock vs. fixture vs. local vs. external data.
4. Run **`scripts/live_agent_demo.py`** to trigger a real Gemini agent run and inspect the recorded evidence.
5. Follow [`docs/demo-script.md`](docs/demo-script.md) for the full guided path.

## 📄 Submission documents

- **[Narrative](docs/xprize-submission-narrative.md)** · [Video script](docs/xprize-video-script.md) · [P&L](docs/xprize-pnl-statement.md) · [Customer evidence](docs/customer-evidence.md)
- [Go-to-market model](docs/pilot-pipeline.md) · [Readiness assessment](docs/xprize-readiness.md) · [Submission checklist](docs/xprize-submission-checklist.md)
- [Architecture](docs/architecture.md) · [Security & privacy](docs/security-and-privacy.md) · [Database schema](docs/database-schema.md) · [Configuration & secrets](docs/configuration-and-secrets.md)

## 🔒 Safety defaults

- Fixture agents and local role switching run only in local/test or explicit demo mode; production forbids them.
- No payment processor is integrated. Coordinators may record independently verified external funding evidence; this does not initiate settlement.
- Production credential issuance requires KMS; local credentials use a disposable gitignored key and are marked demo.
- Credential revocation is append-only; public verification checks the original signature plus revocation history.
- University metrics require an active agreement and consented enrollment; cohorts below the configured minimum are suppressed, including in exports.

## 📝 License

MIT — see [`LICENSE`](LICENSE).
