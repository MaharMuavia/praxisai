# Core product completion audit

Audit baseline: `agent/complete-premium-product-ui` at `fd613f0`, created from the latest premium UI remediation. The implementation branch is `agent/core-product-completion`; `main` is not the starting point.

## Executive finding

The public experience is coherent and the API has real authenticated project, learning, talent, offer, billing, university, operations, credential, notification, and logout workflows. This branch adds persisted public intake, explicit workspace route entry points, capability-aware navigation, typed primary actions, query-key authority, and logout cache clearing. The remaining architectural work is to move page data/mutations out of `AppShell`, extract independent marketing compositions, and add a direct-route permission-denied surface.

The audit does not authorize fictional success states or frontend-only authorization. Public conversion work requires new backend schemas, persistence, rate limiting, audit events, migrations, generated OpenAPI output, and staff review routes before the frontend can claim submission success.

## Findings

### 1. Authenticated routing remains catch-all controlled

- Severity: P0
- User impact: Every authenticated role is rendered through one conditional tree, so loading, errors, permissions, metadata, and primary actions are coupled across unrelated routes.
- Root cause: `apps/web/app/[...slug]/page.tsx` chooses `AppShell` for role roots and `apps/web/components/app-shell.tsx` switches on `path` and `root`.
- Current file: `apps/web/app/[...slug]/page.tsx`, `apps/web/components/app-shell.tsx`.
- Correct owning layer: Next route pages/layouts under an authenticated workspace route group, with shared shell primitives only in the layout.
- Backend dependency: Existing authenticated endpoints are sufficient for initial extraction; public intake is separate.
- Implementation plan: Add explicit pages/layouts for the supported client, student, lead, ops, admin, and university URLs. Keep the catch-all for public compatibility and not-found behavior. Migrate one route family at a time and retain URL compatibility tests.
- Test requirement: Route ownership tests, route-specific query enabling, loading/error/empty/permission states, and all existing public/workspace E2E routes.
- Final verification status: In progress. Explicit route pages now own the URL entry points; the shared `WorkspaceRoute` still delegates rendering to `AppShell`.

### 2. AppShell owns page data and mutations

- Severity: P0
- User impact: Offer decisions, university exports, job recovery, notifications, and project records share mutation state and error messaging; a page failure can affect unrelated shell content.
- Root cause: `apps/web/components/app-shell.tsx` still owns page-specific state and handlers even after `useWorkspaceData` extraction.
- Current file: `apps/web/components/app-shell.tsx`.
- Correct owning layer: Feature/page modules such as projects, offers, billing, operations, and university.
- Backend dependency: Existing mutation endpoints and authorization remain the source of truth.
- Implementation plan: Move each mutation with its query invalidation into the owning feature. Leave AppShell responsible only for session, notification panel, command menu, user menu, drawer, and environment state.
- Test requirement: Mutation success/failure, narrow invalidation, duplicate submission, and shell isolation tests.
- Final verification status: Open. AppShell still owns page-specific mutations and feature rendering.

### 3. Query modules are not authoritative

- Severity: P0
- User impact: Query keys and fetch behavior can drift because `useWorkspaceData` duplicates keys and bypasses the modules under `apps/web/lib/queries`.
- Root cause: The query modules were added as an intended architecture but the compatibility hook reimplemented their keys and fetch calls.
- Current file: `apps/web/components/workspace/use-workspace-data.ts`, `apps/web/lib/queries/*.ts`.
- Correct owning layer: Domain query modules with typed keys, options, mutations, retry classification, and invalidation helpers.
- Backend dependency: Generated client types and existing endpoint contracts.
- Implementation plan: Move route hooks to the existing domain modules, add missing query/mutation options there, and reduce or remove the compatibility hook after page migration. Retry only transient failures and use `AbortSignal` for stale requests.
- Test requirement: Key identity, enabled-state, retry classification, invalidation, and route isolation tests.
- Final verification status: In progress. Domain key factories are now used by the compatibility hook; feature query options and route-level migration remain.

### 4. Generic primary action is unsupported

- Severity: P0
- User impact: The `Next action` button can manufacture a settings-like URL that does not represent the current record or a valid transition.
- Root cause: `AppShell` builds the CTA from `root` and `path` rather than capability, record state, or backend-supported transitions.
- Current file: `apps/web/components/app-shell.tsx`.
- Correct owning layer: Typed workspace action resolvers fed by session capabilities, route, record state, deadlines, and supported transitions.
- Backend dependency: Existing project state/capability contracts; no transition may be inferred only in the browser.
- Implementation plan: Add typed action resolver modules for client, student, lead, operations, admin, and university. Render no primary action when no valid action exists.
- Test requirement: Resolver tests for each role/state/capability combination and a no-action assertion.
- Final verification status: Complete for the implemented resolver paths. Typed resolver tests cover a valid client action and a missing-capability no-action case.

### 5. Navigation is static by role

- Severity: P1
- User impact: Users can see links that their capability set or organization configuration does not support, while direct URL authorization remains backend-only and lacks a useful permission state.
- Root cause: `apps/web/components/workspace-navigation.ts` maps only broad role roots and does not consume membership capabilities, onboarding, or feature availability.
- Current file: `apps/web/components/workspace-navigation.ts`, `apps/web/components/workspace-layout.tsx`.
- Correct owning layer: A typed capability-driven navigation resolver in the frontend, with backend authorization unchanged.
- Backend dependency: Session capability and active membership payloads; permission-denied response classification.
- Implementation plan: Define navigation item metadata, resolve visible links from session state, keep nested matching, and add a permission-denied surface for direct URLs.
- Test requirement: Role/capability matrix, direct forbidden route, nested active state, and sensitive-link non-disclosure tests.
- Final verification status: In progress. Navigation now filters by session capabilities; direct forbidden-route rendering remains to be extracted.

### 6. Logout does not clear authenticated query state

- Severity: P1
- User impact: A successful logout redirects, but active queries and protected cache state are not explicitly cancelled and removed before navigation.
- Root cause: `handleLogout` calls the backend and optional Firebase sign-out but does not use the QueryClient.
- Current file: `apps/web/components/app-shell.tsx`, `apps/web/app/providers.tsx`.
- Correct owning layer: Auth feature/session boundary.
- Backend dependency: Existing `POST /api/v1/auth/logout`.
- Implementation plan: Cancel and remove authenticated query keys, clear local sensitive state, close shell overlays, and replace history before redirect. Preserve public/static query caches.
- Test requirement: Backend/Firebase success and failure, duplicate clicks, cache clearing, redirect, and back-navigation tests.
- Final verification status: Complete in implementation. Logout cancels and clears the React Query cache, closes overlays, replaces history, and redirects.

### 7. Public conversion has no persistence endpoints

- Severity: P0
- User impact: Companies, students, expert leads, and universities cannot submit a real inquiry; the contact page correctly refuses to pretend otherwise.
- Root cause: The inspected API exposes authenticated project creation but no public intent/application/inquiry routes or intake tables.
- Current file: `apps/web/components/content-page.tsx`, `apps/api/app/api/*.py`, `apps/api/app/domain/models.py`.
- Correct owning layer: Public intake API and domain service with validation, rate limiting, idempotency, consent, audit, retention, and operations review.
- Backend dependency: New schemas, model/migration, services, routes, OpenAPI regeneration, and staff review authorization.
- Implementation plan: Add a discriminated intake model or separate typed models for company, student, lead, and university submissions; normalize and persist only required fields; record consent/source/correlation/idempotency; expose privacy-safe acknowledgement responses; add operations queue views.
- Test requirement: Schema, persistence, duplicate/idempotency, rate limit, audit, privacy-safe response, and staff authorization tests.
- Final verification status: Complete in implementation. The API, migration, OpenAPI output, privacy-safe receipt, idempotency, rate limiting, audit event, staff queue, and review tests are present.

### 8. Marketing page composition remains generic in the catch-all

- Severity: P1
- User impact: Major marketing routes are distinct in content but still share a large `ContentPage` conditional composition, making route-specific metadata and testing harder to own.
- Root cause: `apps/web/components/content-page.tsx` contains many route branches.
- Current file: `apps/web/components/content-page.tsx`, `apps/web/app/[...slug]/page.tsx`.
- Correct owning layer: Explicit marketing page compositions with small shared sections.
- Backend dependency: None for static pages; conversion forms depend on public intake APIs.
- Implementation plan: Extract students, companies, pricing, trust, impact, about, contact, and solution page compositions without redesigning the homepage.
- Test requirement: Page-specific content, metadata, responsive, reduced-motion, and CTA destination tests.
- Final verification status: Open. The contact page now has a real intake form, but broader independent page composition remains.

### 9. CI quality contract is not fully deterministic

- Severity: P1
- User impact: Local verification differs from CI; visual snapshots are Windows-specific and Playwright can reuse an existing server.
- Root cause: `apps/web/playwright.config.ts` uses `reuseExistingServer: true` and committed snapshots are `win32`; root format/Ruff checks are not currently passing in the checkout.
- Current file: `apps/web/playwright.config.ts`, `.github/workflows/ci.yml`, existing snapshot directory, root scripts.
- Correct owning layer: Repository/CI configuration.
- Backend dependency: Frozen uv cache and Terraform/provider availability.
- Implementation plan: Use a pinned Linux Playwright project or CI container, freeze locale/time, make the test server owned by the test run, add explicit `format:check`, and fix baseline formatting/Ruff execution.
- Test requirement: Clean-checkout root command run and portable visual snapshots.
- Final verification status: In progress. Repository formatting and lint gates pass, Playwright no longer reuses an existing server, and the production build passes with non-secret placeholders; Windows Playwright child-process cleanup and portable visual baseline work remain.

### 10. Infrastructure verification is not part of the local completion loop

- Severity: P1
- User impact: Application changes can be considered complete without Terraform formatting/initialization/validation evidence.
- Root cause: Terraform checks exist in CI but were not included in the previous local verification report.
- Current file: `infra/terraform/*.tf`, `.github/workflows/ci.yml`.
- Correct owning layer: CI/release verification, without applying infrastructure.
- Backend dependency: Terraform binary and provider initialization only; no apply is authorized.
- Implementation plan: Run fmt-check, init with backend disabled, and validate; record exact results.
- Test requirement: CI-equivalent Terraform checks.
- Final verification status: Unverified locally. Terraform is not installed on this workstation; CI retains fmt, init, and validate checks. No infrastructure apply was attempted.

## Existing strengths to preserve

- The explicit demo environment contract and fallback boundary.
- Human/deterministic authority for consequential workflows.
- Existing backend role authorization and audit/idempotency patterns.
- Premium homepage, marketing navigation, reduced-motion behavior, and truthful claims.
- Generated OpenAPI client workflow and existing route/API tests.

## Delivery order

1. Action resolver and capability-driven navigation primitives.
2. Auth cache clearing and query-module authority.
3. Explicit workspace route ownership and AppShell reduction.
4. Public intake persistence/API, migrations, OpenAPI regeneration, and staff review routes.
5. Public form UX and independent marketing page composition.
6. CI portability, Terraform verification, and repository-wide cleanup.
