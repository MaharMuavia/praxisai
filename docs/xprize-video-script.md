# PraxisAI XPRIZE Video Script

**Target Duration:** 3:00
**Format:** High-speed technical walkthrough on web browser
**Purpose:** XPRIZE Build with Gemini submission

---

### [0:00 - 0:20] Hook
**Visuals:** 
Start on the PraxisAI homepage (`/`) running live on a web browser. The cursor moves purposefully over the hero section and the Interactive workflow model.
**Speaker Notes (Fast, energetic):**
"Welcome to PraxisAI. We're solving the cold-start problem for emerging technical talent. It's an AI-operated apprenticeship studio where students don't just take courses—they deliver paid, verified software and data projects for real companies. Today, we're showing our production MVP built with Gemini."

### [0:20 - 0:50] Architecture overview
**Visuals:** 
Switch to a Mermaid architecture diagram or the `/evidence` page. Show the Next.js frontend, FastAPI backend, PostgreSQL, and Gemini API connections. Highlight the "AI Operations Center" concept. 
**Speaker Notes:**
"Our architecture is a transactional modular monolith. PostgreSQL is the source of truth, and FastAPI domain services manage the state machine. Here’s the key: AI agents are native operators. They don't have direct write access. They propose, draft, and QA using typed schemas. Qualified humans retain authority over all high-risk decisions, preserving accountability and trust."

### [0:50 - 1:40] Live demo - The Judge Path
**Visuals:** 
Navigate to `/judge` (deterministic scenario).
Click through the simulated workflow quickly:
1. **Scope Drafting:** Show a client brief being processed by the "Fixture AI" into a structured scope, with deliverables and exclusions.
2. **Staffing:** Show the deterministic eligibility filter and AI matching proposing a student squad.
3. **Delivery & QA:** Show a submitted milestone and the AI-assisted QA highlighting advisory findings, before a human lead approves the release.
**Speaker Notes:**
"Let's walk through the core delivery loop. When a client submits a brief, our Gemini-powered Scoping agent instantly drafts deliverables, risk exclusions, and clarification questions. Once approved, the Staffing agent matches eligible students based on verified evidence, free from bias. During delivery, the QA agent reviews immutable artifacts against the contract. It provides advisory findings, but a human expert always makes the final release decision."

### [1:40 - 2:20] Operations center & Evidence trail
**Visuals:** 
Navigate to `/ops`. Open the Agent Runs view. 
Show a detailed agent run record: input snapshot, tool calls, structured output, confidence score, token usage, and policy result. 
Switch to the Project Command Center to show the immutable evidence trail and state transitions.
**Speaker Notes:**
"This is the AI Operations Center. Every Gemini agent run is completely auditable. We record the prompt version, input hash, typed structured output, latency, and token usage. Agents run against our typed runtime and strict policy boundaries. If an agent fails, our outbox pattern and dead-letter recovery ensure idempotent retries. The entire project lifecycle generates an append-only cryptographic evidence trail."

### [2:20 - 2:50] Education impact
**Visuals:** 
Log in as student 'Amina Noor'. 
Show the Student Workspace (`/workspace`). Highlight the learning path, sequenced modules, and recorded practice evidence.
Switch to `/verify` to show a cryptographically signed credential with a privacy-safe payload.
**Speaker Notes:**
"For students, PraxisAI is a career accelerator. They complete sequenced modules and build portfolios. When they deliver supervised work, they earn money and undeniable proof of their skills. Our verifiable credentials link directly to the immutable project records and external payout evidence, proving they can deliver real value, not just pass a test."

### [2:50 - 3:00] Close
**Visuals:** 
Back to the homepage hero, or the `/business-model` view showing the sustainable flywheel. Fade to PraxisAI logo.
**Speaker Notes:**
"PraxisAI proves that AI can safely orchestrate complex, real-world apprenticeships at scale. Real preparation. Paid project experience. Verified career proof. Thank you."
