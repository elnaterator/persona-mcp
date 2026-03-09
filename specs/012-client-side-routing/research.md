# Research: Client-Side Routing with Deep Links

**Feature**: 012-client-side-routing
**Date**: 2026-03-06

## R1: Router Library Selection

**Decision**: React Router v7 (library mode, not framework mode)

**Rationale**: React Router is the de facto standard for React SPAs. v7 supports both declarative `<Routes>` and data router patterns (`createBrowserRouter`). Using library mode (declarative `<Routes>`) avoids framework lock-in and integrates naturally with the existing Clerk `<SignedIn>`/`<SignedOut>` wrapper pattern. The `<BrowserRouter>` approach is the simplest migration path from useState-based navigation.

**Alternatives considered**:
- **TanStack Router**: More type-safe but adds complexity; overkill for 7 routes. Smaller ecosystem.
- **Wouter**: Minimal but lacks `<NavLink>` active state support and layout route patterns out of the box.
- **createBrowserRouter (data router mode)**: More powerful (loaders, actions) but requires restructuring data fetching. Current components already fetch data internally — migrating to loaders adds unnecessary churn.

## R2: Router Integration Pattern

**Decision**: Use `<BrowserRouter>` + `<Routes>` declarative pattern wrapping existing components

**Rationale**: The existing app structure uses `<SignedIn>`/`<SignedOut>` from Clerk at the top level. The declarative `<Routes>` pattern nests naturally inside `<SignedIn>`. Components already fetch their own data via `useEffect` — no need for route loaders. The `onSelectResume`/`onBack` callback props get replaced by `<Link>` and `useNavigate()` respectively.

**Alternatives considered**:
- **createBrowserRouter with RouterProvider**: Would require moving Clerk auth context setup and restructuring the component tree. More disruptive for minimal gain at this scale.

## R3: Clerk Auth + Route Protection

**Decision**: Keep existing `<SignedIn>`/`<SignedOut>` pattern; store requested URL for post-login redirect via Clerk's `afterSignInUrl` or `redirectUrl` config

**Rationale**: The current app wraps authenticated content in `<SignedIn>`. This naturally protects all routes. For deep link redirect after sign-in, Clerk's `<SignIn>` component accepts `afterSignInUrl` or the app can store `window.location.pathname` before the auth redirect. Clerk v5+ supports `fallbackRedirectUrl` on the `<ClerkProvider>`.

**Alternatives considered**:
- **Custom route guard component**: Unnecessary — Clerk's `<SignedIn>` already gates all routes. Adding a custom guard would duplicate auth logic.

## R4: Vite Dev Server History Fallback

**Decision**: Vite's dev server enables HTML5 history API fallback by default for SPA mode. No explicit configuration needed.

**Rationale**: Vite's dev server serves `index.html` for any non-file, non-proxied route automatically when running in SPA mode. The existing proxy rules for `/api`, `/health`, `/mcp` take precedence. Verified in Vite documentation — `appType: 'spa'` (the default) enables this behavior.

**Alternatives considered**:
- **Explicit `historyApiFallback` config**: Not needed — Vite handles this by default. Only required if `appType` were set to something other than `'spa'`.

## R5: Breadcrumb Implementation

**Decision**: Create a simple `Breadcrumb` component that accepts label/link pairs. Detail views pass breadcrumb data derived from their fetched entity data.

**Rationale**: The app has a flat two-level hierarchy (section list → item detail). A simple component receiving `{ label: string, to: string }[]` is sufficient. No need for a context-based or route-metadata-based breadcrumb system — the hierarchy is static and predictable.

**Breadcrumb label sources**:
- Resume detail: `version.label` (e.g., "Version 3 — Full-Stack")
- Application detail: `app.company` + " — " + `app.position` (e.g., "Acme Corp — Senior Dev")
- Accomplishment detail: `acc.title` (e.g., "Led Migration to Microservices")

**Alternatives considered**:
- **Route-metadata-based breadcrumbs**: Overcomplicated for 2 levels. Would require coupling breadcrumb labels to route config, which doesn't have access to fetched entity names.
- **useMatches/handle pattern**: React Router supports route `handle` for breadcrumb metadata, but labels depend on runtime data (entity names), not static config.

## R6: Not-Found Handling

**Decision**: Two levels of not-found handling: (1) unknown routes redirect to `/resumes`, (2) valid routes with non-existent IDs show an inline "not found" message in detail views.

**Rationale**: Unknown routes (e.g., `/foo`) should redirect to the default section. For detail views with invalid IDs, the existing data fetch will return a 404 — the detail view components already need error handling, so they can show a "not found" state with a link back to the list. Invalid ID formats (non-numeric) redirect to the section list.

**Alternatives considered**:
- **Dedicated 404 page**: Overkill for this app. Inline not-found messaging within the detail view is simpler and keeps the user in context.
