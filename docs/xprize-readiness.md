# XPRIZE readiness assessment

This assessment distinguishes implemented code from configuration declared in
the repository and from behavior verified against real external services.

## Executive status

PraxisAI is a production-oriented modular-monolith MVP with a meaningful
project-delivery core. It is not yet evidence-ready for the full competition
claim. The largest remaining gaps are real lead intake and admissions, a
complete client-to-paid-student vertical slice, executable supervised agent
actions, hosted provider validation, and source-backed competition evidence.

No repository evidence proves real customers, paying revenue, settled student
earnings, production Gemini usage, Firebase deployment, or a live Google Cloud
deployment. Those claims require authorized source-system records.

## Readiness matrix

| Area | Current status | Required next action |
| --- | --- | --- |
| Modular monolith | Implemented | Preserve web/API/client boundaries |
| Project intake and scope | Partial | Add lead intake, onboarding, acceptance, and funding gate |
| Staffing and offers | Partial | Add evidence-linked scoring, conflict checks, and final human approval |
| Delivery and QA | Partial | Add release gate, completion acceptance, change-order path, and payout test |
| Billing evidence | Partial | Verify funding policy and provider/manual evidence; never infer settlement |
| Credentials | Partial/unverified | Prove KMS signing and eligibility from the complete evidence chain |
| Learning | Partial | Add applications, diagnostics, rubrics, evidence, readiness, and appeals |
| CRM and qualification | Missing | Build the first client lifecycle slice |
| Shared agent runtime | Partial | Add common run contract, typed actions, approvals, auth, cost, retries |
| AI execution | Partial | Execute only policy-checked low-risk actions through outbox and approvals |
| Firebase | Partial/unverified | Run deployed auth, reset, revocation, membership, and rate-limit smoke tests |
| Vertex AI Gemini | Partial/unverified | Verify IAM, structured generation, timeout/error handling, and audit proof |
| Same-origin API routing | Locally implemented; hosted unverified | Deploy and verify Cloud Run routing and IAM behavior |
| Operations | Partial | Add CRM, admissions, funding, release, payout, and risk queues |
| XPRIZE evidence center | Missing | Define versioned source queries, exclusions, exports, and audit trail |
| Observability | Partial | Add recipients and validate request, agent, queue, payment, auth, and DB alerts |
| Security | Partial | Complete hosted threat-model review and provider/security smoke tests |
| Deployment | Terraform locally validated; hosted unverified | Build/publish images and run staging smoke/rollback checks |

## Evidence policy

Demo screenshots and fixtures support product walkthroughs only and must remain
visibly labeled. README and marketing copy must continue to identify cloud
deployment, Gemini, Firebase, email, payment, and real customer/revenue
activity as unverified until source-backed records are attached.
