# PraxisAI company operating model

Status: operating model for implementation planning. Legal, employment, tax, payment, and data-protection language remains subject to qualified review.

## Positioning

PraxisAI is an AI-operated apprenticeship studio. It prepares emerging technical talent through practical, evidence-based learning; forms supervised delivery squads; and delivers paid AI automation, data, software, and lightweight internal-tool projects for real companies.

Primary message:

> Real preparation. Paid project experience. Verified career proof.

Supporting message:

> PraxisAI trains emerging technical talent and deploys supervised student teams to deliver real projects for real companies. AI operates the workflow; qualified humans retain authority over high-risk decisions.

PraxisAI is not a generic course platform, an unrestricted freelance marketplace, or an autonomous employment or project-management system. The company owns scope, staffing, supervision, quality, payment operations, and delivery accountability.

## Commercial wedge

The pilot accepts only constrained projects in four categories:

1. AI workflow automation.
2. Data dashboards and reporting.
3. Internal business tools.
4. Lightweight customer and operations portals.

Every category needs a versioned scope boundary, unsupported-work list, required client inputs, deliverable templates, skill requirements, risk rules, pricing inputs, supervision level, and acceptance-criteria template before it can be offered commercially. High-risk, regulated, deceptive, surveillance, academic-cheating, safety-critical, or otherwise unsuitable work is rejected or routed to manual review.

## Authority model

PostgreSQL is the source of truth. Domain services own authorization, eligibility, money, state transitions, idempotency, concurrency, consent, payment verification, credential issuance, and audit evidence. FastAPI routes authorize and delegate. The Next.js app never writes directly to the database.

AI proposes, explains, summarizes, and executes only explicitly classified low-risk actions after policy checks. Qualified people retain authority for:

- student acceptance, suspension, readiness, and credential decisions;
- final team selection and compensation or project price;
- contractual terms, scope changes, refunds, payouts, and completion acceptance;
- release approval, disputes, appeals, and other decisions that affect access, money, or rights.

Students can decline offers without reputation damage. Consequential decisions must be explainable, auditable, and appealable. Client confidential data is not used for model training.

## Operating lifecycle

### Client and delivery

Visitor lead -> qualification -> verified organization -> structured project request -> proposed scope -> deterministic quote -> human approval -> client acceptance -> funding evidence -> staffing -> approved plan -> supervised delivery -> immutable deliverable evidence -> AI-assisted QA -> human release -> client acceptance or valid revision -> payout approval -> verified payout evidence -> credential eligibility.

No work begins until the configured funding policy is satisfied. Scope changes require a compensated change order. AI cannot issue final client acceptance or claim payment settlement.

### Student and apprenticeship

Application -> identity and policy consent -> target track -> adaptive diagnostic -> versioned rubric review -> deterministic readiness and complexity ceiling -> learning plan -> practical modules and evidence -> human review for high-stakes decisions -> eligibility for paid assignment -> offer with visible pay, hours, deadline, supervision, revisions, and portfolio terms -> supervised delivery -> earnings and verifiable project proof.

Evidence may reference repositories, commits, pull requests, deployments, documents, datasets, notebooks, screenshots, tests, and video explanations. Private contents are not copied unless a specific, consented integration requires them.

## AI operating system

The required agents share one typed runtime, policy boundary, action registry, persistence model, and observability contract. The initial agent set is:

- lead qualification;
- project scope;
- pricing recommendation;
- student diagnostic;
- personalized learning coach;
- matching and squad formation;
- project orchestration;
- QA and release review;
- client success;
- finance operations;
- trust and evidence integrity.

Each run records the agent and prompt versions, model, goal, input snapshot or hash, context references, proposed plan, tool calls and results, structured output, confidence, risk class, policy result, approval requirement and decision, status, retries, token usage, cost estimate, latency, correlation ID, timestamps, and environment/demo provenance.

Low-risk actions include creating draft tasks, reminders, approved-template notifications, learning recommendations, QA defects, missing-evidence requests, summaries, and queue routing. Those actions must be policy-checked, idempotent, auditable mutations—not text-only suggestions.

## Environments and evidence

The environments are separate:

- `local`: developer setup and disposable data;
- `test`: isolated automated-test configuration;
- `demo`: explicit, visibly labeled fictional data and fixture AI;
- `staging`: production-like configuration with real provider boundaries and no fictional fallback;
- `production`: real users, customers, evidence, and secure providers only.

Demo records carry explicit provenance and cannot enter production metrics. Competition evidence must be source-linked to transactional records, define its time window and exclusion policy, and identify the last calculation time. Marketing must not display invented customers, logos, revenue, outcomes, project counts, or testimonials.

## Pilot operating controls

The pilot requires an operations queue for uncertain leads, identity and organization verification, readiness and QA reviews, funding exceptions, release decisions, payouts, disputes, and agent failures. Structured logs, correlation IDs, outbox retries, audit records, evidence hashes, and provider synchronization records support recovery and review.

