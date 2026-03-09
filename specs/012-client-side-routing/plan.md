# Implementation Plan: Client-Side Routing with Deep Links

**Branch**: `012-client-side-routing` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-client-side-routing/spec.md`

## Summary

Replace the `useState`-based navigation in `App.tsx` with React Router v7, adding URL-based routing with deep links to all section lists and detail views. Add breadcrumb navigation to detail views and integrate route protection with existing Clerk authentication.

**Amendment (2026-03-08)**: The original plan assumed this was a frontend-only change — "the backend already serves `index.html` for all non-API routes via `StaticFiles(html=True)`." This assumption was incorrect. Page refresh on any deep route (e.g., `/resumes/3`) returned a 404 in production (Docker), confirming that `StaticFiles(html=True)` does not fall back to `index.html` for arbitrary paths — it only serves files that physically exist on disk. A backend catch-all route is required to serve `index.html` for all non-API, non-asset paths.

## Technical Context

**Language/Version**: TypeScript 5.6 / React 18
**Primary Dependencies**: React Router v7 (new), `@clerk/clerk-react` v5 (existing)
**Storage**: N/A (no storage changes)
**Testing**: Vitest 2 + React Testing Library (existing)
**Target Platform**: Web browser (SPA)
**Project Type**: Web application (frontend-only changes)
**Performance Goals**: Route transitions must feel instant (<100ms perceived); no full-page reloads
**Constraints**: Must preserve existing component APIs; backend change required for SPA fallback (catch-all route)
**Scale/Scope**: 7 routes (4 list + 3 detail), 1 new component (Breadcrumb), modifications to ~5 existing frontend files + 1 backend file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | N/A | Frontend-only change; no MCP tools affected |
| II. Single-Package Distribution | PASS | No backend packaging changes |
| III. Test-Driven Development | PASS | Will write tests for routing, breadcrumbs, and route guards |
| IV. Minimal Dependencies | PASS | React Router is the standard routing library for React; justified by core routing need |
| V. Explicit Error Handling | N/A | No MCP tool handlers changed |
| Makefile targets | PASS | Existing `make check` in frontend/ covers lint + test |
| Branch naming | PASS | `012-client-side-routing` follows accepted pattern |
| Conventional commits | PASS | Will use `feat:` prefix |
| README updates | PASS | Will include task to update README with routing info |

**Result**: All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/012-client-side-routing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (route map)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.tsx                          # MODIFY: Replace useState nav with <BrowserRouter> + <Routes>
│   ├── router.tsx                       # NEW: Route definitions and layout
│   ├── components/
│   │   ├── Navigation.tsx               # MODIFY: Replace button onClick with <NavLink>
│   │   ├── Breadcrumb.tsx               # NEW: Breadcrumb component
│   │   ├── Breadcrumb.module.css        # NEW: Breadcrumb styles
│   │   ├── NotFound.tsx                 # NEW: "Item not found" component
│   │   ├── NotFound.module.css          # NEW: NotFound styles
│   │   ├── ResumeListView.tsx           # MODIFY: Remove onSelectResume prop, use <Link>
│   │   ├── ResumeDetailView.tsx         # MODIFY: Remove onBack prop, use useParams + useNavigate
│   │   ├── ApplicationListView.tsx      # MODIFY: Remove onSelectApp prop, use <Link>
│   │   ├── ApplicationDetailView.tsx    # MODIFY: Remove onBack prop, use useParams + useNavigate
│   │   ├── AccomplishmentListView.tsx   # MODIFY: Remove onSelectAccomplishment prop, use <Link>
│   │   ├── AccomplishmentDetailView.tsx # MODIFY: Remove onBack prop, use useParams + useNavigate
│   │   └── ConnectView.tsx              # NO CHANGE
│   ├── services/
│   │   └── api.ts                       # NO CHANGE
│   └── __tests__/
│       └── components/
│           ├── Navigation.test.tsx      # MODIFY: Update for NavLink
│           ├── Breadcrumb.test.tsx       # NEW: Breadcrumb tests
│           ├── routing.test.tsx          # NEW: Route integration tests
│           └── NotFound.test.tsx         # NEW: NotFound tests
├── vite.config.ts                       # NO CHANGE (Vite SPA mode handles history fallback by default in dev)
└── package.json                         # MODIFY: Add react-router dependency
backend/
├── src/persona/
│   └── api/
│       └── routes.py                    # MODIFY: Add GET /{path:path} catch-all route returning index.html
│   └── server.py                        # VERIFY: Confirm route mount order ensures API routes take priority
└── tests/
    └── integration/
        └── test_spa_fallback.py         # NEW: Verify /resumes, /resumes/3, etc. return 200 HTML
```

**Structure Decision**: Primarily frontend changes. One backend file modified to add a catch-all SPA fallback route. New files are minimal (router definition, breadcrumb component, not-found component, integration test). Most work is modifying existing frontend components to use router APIs instead of callback props.
