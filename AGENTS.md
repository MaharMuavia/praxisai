# PraxisAI engineering guide

- `apps/web`: Next.js user interface. Keep domain decisions out of components.
- `apps/api`: FastAPI application. Routes authorize and delegate to domain services.
- `packages/api-client`: generated OpenAPI types and client.
- `infra/terraform`: Google Cloud baseline; never apply without operator approval.
- `docs`: architecture, security, contracts, and operator guidance.

Use strict TypeScript and typed Python. Validate all boundaries. AI providers may only return proposals; deterministic services own workflow changes. Money is integer minor units plus ISO currency. Append-only financial, audit, consent, reputation, and agent records are never rewritten.

Run `npm run format`, `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build` before handoff. Add an Alembic migration for every database change and regenerate the API client after changing OpenAPI. Never enable local auth, fixture AI, demo signing, or live payment settings in production.

