# PraxisAI: An AI-Operated Apprenticeship Studio
*Submission for XPRIZE Build with Gemini - Education & Human Potential*

## 1. The Challenge and Our Solution
The transition from learning to earning in technical fields is broken by a paradox: employers require experience, but candidates need employment to gain it. Course platforms offer theory without stakes; open freelance marketplaces offer stakes without supervision, and bypass anyone without an established portfolio.

**PraxisAI** operates an AI-driven apprenticeship studio connecting practical learning directly to paid, supervised project work. *Real preparation. Paid project experience. Verified career proof.*

We are not a course platform or a marketplace. We are an integrated studio that owns scope, staffing, supervision, quality, payment operations, and delivery accountability. Constraining initial projects to AI workflow automation, data dashboards, and internal business tools keeps acceptance criteria checkable — a safety property as much as a commercial one — so students can deliver real value under supervision and leave with a verifiable credential.

## 2. Gemini Agents at the Core of Business Operations
Gemini agents share a single typed runtime, policy boundary, and observability contract. 

Our custom Gemini adapter currently drives four production-designed agent workflows:
- **Project Scoping:** Ingests unstructured client requests and drafts deliverables, acceptance criteria, assumptions, exclusions, required skills, effort range, risk items, and clarification questions.
- **Delivery Planning:** Decomposes an accepted scope into milestones and tasks, covering every acceptance criterion and preserving dependency order.
- **QA Review:** Assesses immutable artifact metadata and deterministic evidence against the accepted scope, returning per-criterion findings.
- **Multimodal QA:** Accepts a screenshot, PDF, or diagram alongside the rubric and returns structured visual findings — layout, legibility, and criterion fulfilment — using Gemini's native multimodal input.

Every call uses enforced structured output (`response_schema`), not string parsing, so malformed model output fails closed rather than entering the database. Each run records the model identifier, prompt version, input snapshot hash, latency, token usage, retry count, and correlation ID in an append-only `agent_runs` table, giving full auditability of what the model was asked and what it returned.

Agents for student diagnostics, coaching, and squad matching are designed but **not yet implemented**; those workflows are currently deterministic or human-run.

## 3. Human-AI Workflow Division
While Gemini handles the heavy lifting of drafting, summarizing, analyzing, and proposing, PraxisAI enforces a strict authority model where qualified humans retain control over consequential decisions. 

**AI Handles:**
- Drafting bounded scopes, acceptance criteria, and milestone plans from raw client briefs.
- Analyzing submitted deliverable artifacts — including screenshots and documents — and returning structured, per-criterion QA findings.
- Writing proposals into the database as versioned, `PROPOSED`-status records that a human must accept before they take effect.

Today the boundary is strict: **no agent commits a business decision autonomously.** Every run is stored with `human_approval_required = true` and an empty `executed_action_evidence` list. The supervision schema is deliberately built to record autonomous execution — proposed actions, executed-action evidence, and the approval flag are first-class, audited columns — so that specific low-risk actions can be promoted to agent execution with a full evidence trail once each has an operational track record. We have not promoted any yet, and the schema records that honestly rather than overstating it.

**Humans (Coordinators & Clients) Retain Authority Over:**
- **Money & Contracts:** Final project price, contractual terms, scope changes, refunds, and payouts.
- **Admissions & Credentials:** Student acceptance, readiness approvals, suspension, and the issuance of verified credentials.
- **Quality & Release:** Final team selection, completion acceptance, release approval, and dispute resolution.

Our API delegates state transitions to domain services that enforce workflow guards; agents consume typed inputs and emit typed proposals, with no mutation tools for high-risk actions.

## 4. Unlocking Future Economic Opportunities
The model is designed so that students do not merely earn a certificate — they earn money and build a verified professional record. **No student has yet been paid through PraxisAI; no payment processor is integrated.** What follows describes the delivery flow the platform implements, not outcomes it has produced.

On project completion, the student receives immutable deliverable evidence, pay records, and a cryptographically signed W3C Verifiable Credential. Credential issuance, revocation, and public verification are built and tested: verification re-checks the original signature against append-only revocation history. The intent is to give employers checkable proof of delivered work rather than a self-reported claim. 

As the studio scales, the AI-operated model reduces the coordinator overhead that caps how many projects one supervisor can run — the single variable the business model is most sensitive to. That unlocks lightweight technical work for small businesses previously priced out of custom development, and creates a recurring supply of paid opportunities for students.

## 5. Current Stage and Truthful Execution
We will not invent revenue figures, customer counts, or partnerships, so here is the position plainly.

**What is real:** a Next.js web application, a FastAPI transactional API, and 100 PostgreSQL tables under a single Alembic head. Four Gemini workflows built on the `google-genai` SDK with enforced response schemas, versioned prompts, bounded retries, and per-run audit records. Append-only audit trails, escrow ledger, credential signing and revocation, role-based authorization, and per-user rate limits. 230 automated tests passing locally. Terraform defining the full Google Cloud footprint — Cloud Run, Secret Manager, KMS, Cloud Storage, Cloud Scheduler, and monitoring alerts. Production configuration that refuses to boot if fixture AI or demo mode is enabled.

**What is not:** PraxisAI has **no revenue, no users, no signed partners, and is not yet deployed.** No production Gemini request has been served. Our P&L for the competition window reports $0 revenue against roughly $113 in costs, and `docs/pilot-pipeline.md` presents a commercial model with explicitly zero committed customers.

We would rather be measured on what we can show than on what we could claim. The engineering that makes an AI-supervised apprenticeship studio safe — bounded agent authority, verifiable delivery evidence, and an audit trail for every model decision — is built and testable today. Commercial validation is the next milestone, not a completed one.
