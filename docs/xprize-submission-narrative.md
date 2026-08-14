# PraxisAI: An AI-Operated Apprenticeship Studio
*Submission for XPRIZE Build with Gemini - Education & Human Potential*

## 1. The Challenge and Our Solution
The transition from learning to earning in technical fields is fundamentally broken. Emerging technical talent often faces a paradox: employers require experience, but candidates need employment to gain experience. Generic course platforms offer theoretical knowledge without practical stakes, while unrestricted freelance marketplaces often lead to a race to the bottom, bypassing those without an established portfolio.

**PraxisAI** solves this by operating an AI-driven apprenticeship studio. We connect practical learning directly to paid, supervised project work. 

Our core proposition is simple: *Real preparation. Paid project experience. Verified career proof.* 

We train emerging technical talent and deploy supervised student teams to deliver real projects for real companies. PraxisAI is not a course platform or a freelance marketplace; it is an integrated studio that owns the scope, staffing, supervision, quality, payment operations, and delivery accountability. By constraining initial projects to AI workflow automation, data dashboards, and internal business tools, we provide a structured environment where students can safely deliver value, earn real money, and build a verified, cryptographic credential of their capabilities.

## 2. Gemini Agents at the Core of Business Operations
Gemini AI agents are deeply integrated into PraxisAI’s core business operations, sharing a single typed runtime, policy boundary, action registry, and observability contract. 

Our custom Gemini adapter drives a multi-agent system that includes:
- **Lead Qualification & Project Scoping:** Agents ingest unstructured client requests to draft deliverables, criteria, assumptions, exclusions, skills, effort, risk, and clarification questions.
- **Student Diagnostics & Coaching:** Agents provide adaptive diagnostics and personalized learning plans based on versioned rubrics, evaluating student readiness.
- **Matching and Squad Formation:** Gemini agents recommend team compositions based on verified skills, availability, and project requirements.
- **Project Orchestration & QA Review:** Agents monitor delivery, verify immutable artifact metadata, and provide advisory QA findings against the accepted scope.

This deep integration allows PraxisAI to scale the personalized attention traditionally required in apprenticeships. Each agent run records prompt versions, context references, tool calls, structured outputs, confidence levels, and token usage, ensuring full auditability of the AI’s decision-making process.

## 3. Human-AI Workflow Division
While Gemini handles the heavy lifting of drafting, summarizing, analyzing, and proposing, PraxisAI enforces a strict authority model where qualified humans retain control over consequential decisions. 

**AI Handles:**
- Generating draft scopes, pricing recommendations, and project milestones.
- Analyzing student code, notebooks, and evidence to provide immediate feedback.
- Proposing student-project matches based on deterministic eligibility filtering.
- Conducting first-pass QA on deliverables and drafting client communications.
- Executing explicitly classified low-risk actions (e.g., creating draft tasks, sending approved-template notifications).

**Humans (Coordinators & Clients) Retain Authority Over:**
- **Money & Contracts:** Final project price, contractual terms, scope changes, refunds, and payouts.
- **Admissions & Credentials:** Student acceptance, readiness approvals, suspension, and the issuance of verified credentials.
- **Quality & Release:** Final team selection, completion acceptance, release approval, and dispute resolution.

This division ensures safety, accountability, and trust. Our API delegates business state transitions to domain services that enforce workflow guards, while AI agents consume typed inputs and produce typed proposals without mutation tools for high-risk actions.

## 4. Unlocking Future Economic Opportunities
PraxisAI goes beyond the initial pilot phase to create lasting economic opportunities for its users. By participating in PraxisAI, students do not just earn a certificate; they earn real money and build a verified professional record of their work. 

When a project concludes, the student receives immutable deliverable evidence, pay records, and a cryptographically signed credential. This verifiable proof transforms how emerging talent enters the technical workforce, providing employers with irrefutable evidence of a candidate's ability to deliver real-world business value. 

Furthermore, as PraxisAI scales, the AI-operated model drastically reduces the overhead of project management and technical supervision. This allows the studio to take on an increasing volume of lightweight technical projects from small-to-medium businesses that previously could not afford custom development. This expanding marketplace creates a sustainable economic engine where students continually find paid opportunities to refine their skills, and businesses access high-quality, supervised technical talent at a competitive price.

## 5. Current Stage and Truthful Execution
PraxisAI is currently in the pilot stage. The platform is an in-progress, production-oriented MVP consisting of a Next.js web application, a FastAPI transactional API, and PostgreSQL persistence. We have implemented vertical slices of the core loop and established a secure, auditable foundation where all local role switching and agent fixtures run in explicit demo modes. 

We do not invent revenue figures or customer counts. The commercial wedge is strictly constrained to specific, manageable project categories, and the deployment is poised for production validation. PraxisAI is built on a solid architectural foundation that prioritizes safety, determinism, and verifiable outcomes—ready to demonstrate how Gemini can safely bridge the gap between education and meaningful economic participation.
