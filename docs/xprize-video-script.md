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
Navigate to `/judge` (deterministic, pre-scripted illustrations — labeled as such).
Click through quickly:
1. **Scope Drafting:** Show a client brief becoming a structured scope with deliverables and exclusions. Then click the **Policy Rejected** and **Prompt Injection** presets to show the boundary containing an unsafe request.
2. **Multimodal QA:** Upload a deliverable screenshot; show Gemini returning structured, per-criterion visual findings (layout, contrast, tap targets).
3. **Human boundary:** Show the QA finding is *advisory* — a human lead approves release; the agent record shows `human_approval_required`.
**Speaker Notes:**
"Let's walk the delivery contract. A client brief becomes a structured scope with deliverables, risks, and clarification questions — and because every brief is treated as untrusted data, watch the policy engine reject a restricted request and contain a prompt-injection attempt. Then the part we're proudest of: Gemini's native multimodal QA reads a deliverable screenshot and returns structured findings on layout, contrast, and responsive defects. Every finding is advisory — a human expert makes the final release decision. Agents propose; people decide."

### [1:40 - 2:20] Operations center & Evidence trail
**Visuals:** 
Navigate to `/ops/agent-runs`. Open the agent run inspector. 
Show a real agent run record: agent name, model identifier, prompt version, input-snapshot hash, typed structured output, latency, token usage, retry count, and the human-boundary state. 
Switch to the Project Command Center to show the immutable evidence trail and state transitions.
**Speaker Notes:**
"This is the operations center. Every Gemini run is recorded in an append-only table — the model, prompt version, input-snapshot hash, typed structured output, latency, token usage, and retry count — with structured output enforced by schema so malformed responses fail closed. Each record also carries the authority boundary: approval required, no action executed by the agent. If a run fails, our outbox pattern and dead-letter recovery ensure idempotent retries."

### [2:20 - 2:50] Education impact
**Visuals:** 
Log in as student 'Amina Noor'. 
Show the Student Workspace (`/workspace`). Highlight the learning path, sequenced modules, and recorded practice evidence.
Switch to `/verify` to show a cryptographically signed credential with a privacy-safe payload.
**Speaker Notes:**
"For students, PraxisAI is designed as a career accelerator: complete sequenced modules, build practice evidence, and — when they deliver supervised project work — earn a cryptographically signed credential tied to the immutable project record. That credential is real and verifiable today; its signature and revocation history check on the public verify page. We're pre-revenue and pilot-stage, so no student has been paid through the platform yet — the delivery and credential machinery that makes it possible is what's built."

### [2:50 - 3:00] Close
**Visuals:** 
Back to the homepage hero, or the `/business-model` view showing the sustainable flywheel. Fade to PraxisAI logo.
**Speaker Notes:**
"PraxisAI shows how Gemini can safely operate the hard parts of an apprenticeship studio — scoping, planning, and multimodal QA — inside strict human authority boundaries, with every decision audited. Real preparation. Paid project experience. Verified career proof. That's the model we've built and the pilot we're ready to run. Thank you."
