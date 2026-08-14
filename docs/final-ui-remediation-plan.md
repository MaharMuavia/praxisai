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
- `apps/web/components/workspace/use-workspace-data.ts`
- `apps/web/lib/demo-environment.ts`
- `apps/web/lib/demo-data.ts`
- focused component, responsive, visual-regression, and end-to-end tests

## Correct implementation

Use a typed environment contract for explicit demo mode and recoverable demo fallback. Render demo copy only when that contract or an actual fallback says the data is fictional. Use the extracted workspace header and sidebar as the single shell implementation. Make search a clearly scoped local command menu over loaded records and navigation. Route logout through the existing API endpoint, optionally clear Supabase Auth state, surface a correlation id on failure, and redirect to login after success. Use nested-route matching, a focus-trapped mobile drawer, standard disclosure navigation for marketing menus, keyed panel transitions, visibility-aware workflow playback, and requestAnimationFrame-throttled scroll progress.

Move route-owned workspace reads into independently enabled React Query lifecycles. Keep recoverable demo fallback inside the typed data boundary, and let only the active route's query error block its main panel. The current API supports authenticated company project intake and logout. It does not expose a public company-intent or student-application endpoint, so public CTAs must link to the supported login/intake path or remain informational.

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
- Full web Playwright run: 73 tests passed, including all existing public/workspace coverage and the new responsive/visual checks.
- Responsive/accessibility browser coverage: 7 tests passed at 320, 375, 768, 1024, and 1440px, including overflow, landmark, image-alt, workspace-shell, and keyboard-navigation assertions.
- Visual regression coverage: stable home and trust page snapshots added and verified with Playwright.
- Root `format`: failed on 24 pre-existing unformatted files outside this remediation; changed files were formatted and explicit checks passed.
- Root `lint`: web lint passed; the backend Ruff step was blocked by the local uv cache permission before it could run.
- Root `typecheck`: passed; generated API client, web TypeScript, and backend mypy all passed.
- Root `build`: passed with the explicit local demo contract.
- Root `test`: passed after elevated Vitest/uv execution (36 web tests and 56 backend tests).
- Root `test:e2e` delegates to the verified web Playwright command above; the direct web command passed with the existing dev server on port 3000.

The implementation is intentionally honest about remaining architecture work. AppShell still owns mutations and presentation, but its route data reads now run through `useWorkspaceData` and independently enabled React Query lifecycles. Public company intake and student application remain backend-blocked because the inspected API has no public endpoints for them. Automated axe checks and Lighthouse/Core Web Vitals measurements were not added or claimed in this pass.
