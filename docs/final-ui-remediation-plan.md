# Final UI remediation plan

## Confirmed issue

The authenticated shell still renders a `Demo data` badge for every workspace, even when the API returns real data. The sidebar also falls back to `Demo environment` when the session has not loaded. The shell duplicates the extracted header implementation, the workspace search field does not perform a truthful search, logout is decorative, nested navigation paths are not active, and the mobile drawer has no focus trap. Marketing disclosure menus use application-menu roles without implementing the full keyboard model. Motion panels do not remount on content changes, workflow autoplay does not pause on hidden tabs, and scroll progress updates on every scroll event.

## Root cause

Demo state is inferred in component rendering instead of coming from one explicit environment contract. AppShell owns data fetching, shell rendering, and mutations in one client component, so the extracted workspace components are not authoritative. Several interaction primitives were styled before their state, focus, and error behavior was completed.

## Files affected

- `apps/web/components/app-shell.tsx`
- `apps/web/components/workspace-layout.tsx`
- `apps/web/components/workspace-navigation.ts`
- `apps/web/components/marketing-nav.tsx`
- `apps/web/components/motion.tsx`
- `apps/web/components/marketing-workflow.tsx`
- `apps/web/lib/demo-environment.ts`
- `apps/web/lib/demo-data.ts`
- focused component and end-to-end tests

## Correct implementation

Use a typed environment contract for explicit demo mode and recoverable demo fallback. Render demo copy only when that contract or an actual fallback says the data is fictional. Use the extracted workspace header and sidebar as the single shell implementation. Make search a clearly scoped local command menu over loaded records and navigation. Route logout through the existing API endpoint, optionally clear Firebase state, surface a correlation id on failure, and redirect to login after success. Use nested-route matching, a focus-trapped mobile drawer, standard disclosure navigation for marketing menus, keyed panel transitions, visibility-aware workflow playback, and requestAnimationFrame-throttled scroll progress.

The current API supports authenticated company project intake and logout. It does not expose a public company-intent or student-application endpoint, so public CTAs must link to the supported login/intake path or remain informational.

## Tests required

- Explicit demo, test, staging, production, fallback, and real-data label behavior.
- Logout request, pending state, redirect, and correlation-id error handling.
- Scoped workspace search and navigation results.
- Nested active-route matching.
- Mobile drawer focus trapping, Escape/backdrop close, body-scroll lock, and focus restoration.
- Marketing disclosure keyboard behavior and focus restoration.
- Keyed animated panel replacement, reduced motion, workflow hidden-tab pause, and throttled scroll progress.
- Public route CTA honesty and authenticated company intake reachability.

## Whether backend support exists

Logout exists at `POST /api/v1/auth/logout`. Authenticated company project creation exists at `POST /api/v1/projects`. The inspected API does not provide a public company project-intent endpoint or student application endpoint. No new database migration or OpenAPI regeneration is required for this frontend remediation.

## Verification result after implementation

- Web TypeScript typecheck: passed.
- Web ESLint: passed.
- Web unit/component suite: passed, 15 files and 36 tests.
- Backend mypy: passed, 63 source files.
- Backend pytest: passed, 56 tests.
- Production build: passed with the repository's explicit local demo contract (`NEXT_PUBLIC_APP_ENV=demo`, `NEXT_PUBLIC_DEMO_MODE=true`).
- Clean web Playwright run: all 66 tests reported `ok`.
- Root `format`: failed on 24 pre-existing unformatted files outside this remediation; changed files were formatted and explicit checks passed.
- Root `lint`: web lint passed; the backend Ruff step was blocked by the local uv cache permission before it could run.
- Root `test`: passed after elevated Vitest/uv execution.
- Root `test:e2e`: a rerun was invalidated by a stale dev server left on port 3000 and timed out after switching to port 3001; the clean web run remains the verified browser result.

The implementation is intentionally honest about remaining architecture work. AppShell still contains the existing role-data orchestration and has not been fully converted to route-owned React Query hooks. Public company intake and student application remain backend-blocked because the inspected API has no public endpoints for them. Visual regression screenshots, automated axe checks, and Lighthouse/Core Web Vitals measurements were not added or claimed in this pass.
