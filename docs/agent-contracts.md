# Agent contracts

`AgentProvider.generate_structured` accepts an agent name, prompt version, trusted system instruction, typed input model, typed output schema, and correlation ID. The provider returns validated output plus model, latency, retry, and provider-supplied usage metadata.

- Scoping drafts deliverables, criteria, assumptions, exclusions, skills, effort, risk, and clarification questions. Deterministic policy and pricing services decide eligibility and money.
- Staffing runs only after deterministic eligibility filtering. Protected attributes are excluded. Configured weights and evidence counts remain visible to coordinators.
- Planning output must cover every criterion, remain within dates and scope, and have an acyclic dependency graph.
- QA begins with immutable artifact metadata and deterministic evidence. AI findings are advisory and remain distinct from lead and coordinator decisions.
- Credential summaries use verified records only. A deterministic service applies consent, canonicalizes, hashes, and signs the public payload.

Client briefs, repository text, uploaded artifacts, and model output are untrusted data. They are delimited as data, redacted before storage, and never interpreted as system instructions or mutation commands. Tests use sanitized fixtures and do not call Gemini.

