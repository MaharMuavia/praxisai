# Contributing to PraxisAI

## Development contract

Create a focused branch, keep business logic out of route and UI layers, and
preserve the existing FastAPI, SQLAlchemy, Alembic, Next.js, React Query, and
generated-client boundaries. AI output is a proposal; deterministic services
own state transitions. Never commit secrets or represent fixture activity as
production evidence.

Database changes require an Alembic migration. OpenAPI changes require a
regenerated `openapi.json` and `packages/api-client/src/schema.ts`. Add or update
tests for every behavior change.

Before opening a pull request, run:

```text
npm run format
npm run lint
npm run typecheck
npm test
npm run build
```

Run the relevant integration, Playwright, Terraform, container, and security
checks when the changed surface requires them. Do not update a visual snapshot
until the expected, actual, and diff images have been reviewed.

## Pull requests

Explain the user-visible outcome, architectural decisions, migrations, security
impact, and actual verification results. Link the issue or decision record when
one exists. Keep unrelated changes out of the pull request.

By contributing, you confirm that you have the right to submit the contribution
under the repository's owner-approved license once that license is published.
