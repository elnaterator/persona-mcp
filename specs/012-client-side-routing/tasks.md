# Tasks: Client-Side Routing with Deep Links

**Input**: Design documents from `/specs/012-client-side-routing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/routes.md

**Tests**: Test tasks included per constitution TDD mandate (Principle III).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install React Router and create project scaffolding

- [X] T001 Install react-router dependency in `frontend/package.json`
- [X] T002 [P] Create route definitions file at `frontend/src/router.tsx` with BrowserRouter, Routes, and all route paths per contracts/routes.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rewire App.tsx to use router instead of useState-based navigation. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Refactor `frontend/src/App.tsx` — remove `View` type, `useState<View>`, `handleNavigate`, and conditional rendering; wrap entire app in `<BrowserRouter>` OUTSIDE `<ClerkProvider>`, place `<Routes>` inside `<SignedIn>`, add layout with header (Navigation + UserMenu) and child routes per contracts/routes.md
- [X] T004 Refactor `frontend/src/components/Navigation.tsx` — replace `<button>` onClick handlers with `<NavLink to="/resumes">` etc.; remove `onNavigate` prop; use NavLink active class for styling per navigation contracts

**Checkpoint**: App renders with router, section nav works via URL, but list→detail navigation still uses old callbacks

---

## Phase 3: User Story 1 — URL-Based Navigation Between Sections (Priority: P1) 🎯 MVP

**Goal**: Browser URL reflects current section, back/forward buttons work, page refresh preserves location

**Independent Test**: Click between nav sections — URL changes; back button returns to previous section; F5 preserves location

### Implementation for User Story 1

- [X] T005 [US1] Add root redirect (`/` → `/resumes`) and catch-all redirect (`*` → `/resumes`) in route definitions in `frontend/src/router.tsx` or `frontend/src/App.tsx`
- [X] T006 [US1] Verify Navigation active state styling works with NavLink in `frontend/src/components/Navigation.tsx` — ensure `activeView` logic is replaced by NavLink's built-in active class matching (path starts with `/resumes`, `/applications`, etc.)
- [X] T007 [US1] Update `frontend/src/components/Navigation.module.css` if needed to style NavLink active state (replace any button-specific active styles with NavLink-compatible selectors)

- [X] T007a [US1] Write route integration tests in `frontend/src/__tests__/routing.test.tsx` — test root redirect, catch-all redirect, section navigation renders correct views, back/forward behavior

**Checkpoint**: Section-level URL routing works — clicking nav updates URL, back button works, refresh preserves section

---

## Phase 4: User Story 2 — Deep Links to Detail Views (Priority: P1)

**Goal**: Each detail view has a unique URL (`/resumes/:id`, `/applications/:id`, `/accomplishments/:id`); bookmarks and shared links work

**Independent Test**: Navigate to a detail view, copy URL, open in new tab — same item loads; visit `/resumes/999` — see not-found message

### Implementation for User Story 2

- [X] T008 [P] [US2] Create NotFound component at `frontend/src/components/NotFound.tsx` — accepts `entityName`, `backTo`, `backLabel` props; renders user-friendly message with Link back to list
- [X] T009 [P] [US2] Create NotFound styles at `frontend/src/components/NotFound.module.css`
- [X] T010 [P] [US2] Refactor `frontend/src/components/ResumeListView.tsx` — remove `onSelectResume` prop; replace click handler with `<Link to={`/resumes/${id}`}>` for each item
- [X] T011 [P] [US2] Refactor `frontend/src/components/ResumeDetailView.tsx` — remove `versionId` and `onBack` props; use `useParams()` to extract `id` from URL; use `useNavigate()` or `<Link to="/resumes">` for back; validate ID is numeric (redirect to `/resumes` if not); show NotFound for 404 API responses
- [X] T012 [P] [US2] Refactor `frontend/src/components/ApplicationListView.tsx` — remove `onSelectApp` prop; replace click handler with `<Link to={`/applications/${id}`}>`
- [X] T013 [P] [US2] Refactor `frontend/src/components/ApplicationDetailView.tsx` — remove `appId` and `onBack` props; use `useParams()` to extract `id`; use `useNavigate()` or `<Link to="/applications">` for back; validate ID is numeric; show NotFound for 404
- [X] T014 [P] [US2] Refactor `frontend/src/components/AccomplishmentListView.tsx` — remove `onSelectAccomplishment` prop; replace click handler with `<Link to={`/accomplishments/${id}`}>`
- [X] T015 [P] [US2] Refactor `frontend/src/components/AccomplishmentDetailView.tsx` — remove `accomplishmentId` and `onBack` props; use `useParams()` to extract `id`; validate ID is numeric; show NotFound for 404
- [X] T016 [US2] Remove stale callback prop types and wiring from `frontend/src/App.tsx` — clean up any remaining prop-drilling for selection/back callbacks that are no longer used
- [X] T016a [P] [US2] Write NotFound component tests in `frontend/src/__tests__/NotFound.test.tsx` — test rendering with different entityName/backTo/backLabel props, verify back link target
- [X] T016b [US2] Add deep link tests to `frontend/src/__tests__/routing.test.tsx` — test `/resumes/:id` renders detail view, invalid ID redirects to list, non-existent ID shows NotFound

**Checkpoint**: Deep links work — navigating to `/resumes/3` loads resume 3; bookmarking and sharing URLs works; invalid IDs handled

---

## Phase 5: User Story 3 — Breadcrumb Navigation (Priority: P2)

**Goal**: Detail views display breadcrumb navigation showing hierarchy (e.g., "Resumes > Version 3 — Full-Stack") with clickable segments

**Independent Test**: Navigate to a detail view — breadcrumbs appear with correct labels; click section breadcrumb — navigates to list view; list views show no breadcrumbs

### Implementation for User Story 3

- [X] T017 [P] [US3] Create Breadcrumb component at `frontend/src/components/Breadcrumb.tsx` — accepts `items: { label: string; to?: string }[]`; renders clickable Link segments separated by ">"; last segment is plain text
- [X] T018 [P] [US3] Create Breadcrumb styles at `frontend/src/components/Breadcrumb.module.css`
- [X] T019 [US3] Add Breadcrumb to `frontend/src/components/ResumeDetailView.tsx` — render `[{ label: "Resumes", to: "/resumes" }, { label: version.label }]`
- [X] T020 [US3] Add Breadcrumb to `frontend/src/components/ApplicationDetailView.tsx` — render `[{ label: "Applications", to: "/applications" }, { label: "{company} — {position}" }]`
- [X] T021 [US3] Add Breadcrumb to `frontend/src/components/AccomplishmentDetailView.tsx` — render `[{ label: "Accomplishments", to: "/accomplishments" }, { label: acc.title }]`

- [X] T021a [US3] Write Breadcrumb component tests in `frontend/src/__tests__/Breadcrumb.test.tsx` — test rendering with multiple items, last item as plain text, clickable Link segments, empty items array

**Checkpoint**: Breadcrumbs display on all detail views with correct labels and working navigation links

---

## Phase 6: User Story 4 — Authenticated Route Protection (Priority: P2)

**Goal**: Unauthenticated users see landing/sign-in page for all routes; post-sign-in redirects to originally requested URL

**Independent Test**: Visit `/resumes/1` while signed out — see sign-in page; sign in — land on `/resumes/1`

### Implementation for User Story 4

- [X] T022 [US4] Configure Clerk post-sign-in redirect in `frontend/src/main.tsx` — set `signInFallbackRedirectUrl` on `<ClerkProvider>` to `window.location.pathname + window.location.search` so deep links are preserved through the auth flow
- [X] T023 [US4] Verify `<SignedOut>` wrapping in `frontend/src/App.tsx` covers all routes — ensure unauthenticated access to any URL shows LandingPage (existing pattern should work; verify no routes leak outside `<SignedIn>`)

**Checkpoint**: Auth protection complete — deep links through sign-in flow work; no routes accessible without authentication

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, type updates, and validation

- [X] T024 [P] Update TypeScript types in `frontend/src/types/` — remove any `View` type, `NavSection` type, or callback prop types that are no longer used
- [X] T025 [P] Update existing tests in `frontend/src/__tests__/` — fix any broken tests due to removed props or changed component APIs (Navigation, list views, detail views)
- [X] T025a Update `README.md` with client-side routing documentation — document available routes, deep link format, and breadcrumb behavior
- [X] T026 Run `make check` from repository root — ensure lint, typecheck, and all tests pass
- [ ] T027 Run quickstart.md verification steps — manually verify all 8 scenarios listed in quickstart.md

---

## Phase 8: User Story 5 — Direct URL Loading Without 404 (Priority: P1)

**Goal**: Any app URL accessed directly — via browser refresh, address bar, bookmark, or shared link — loads the correct view. The server never returns a 404 for a valid app route in any environment (dev, Docker, production).

**Context**: Page-refresh 404 was confirmed in production. The original plan assumed `StaticFiles(html=True)` handled this, but it only serves files that exist on disk; it does not fall back to `index.html` for arbitrary paths like `/resumes/3`. A backend catch-all route is required.

**Independent Test**: With the app running via `make run` (Docker), navigate to `/accomplishments/2`, press F5 — the page reloads and shows the accomplishment detail view, not a 404.

### Implementation for User Story 5

- [X] T028 [US5] Audit backend static file serving in `backend/src/persona/server.py` — confirm that `StaticFiles(html=True)` does NOT serve `index.html` as a fallback for paths like `/resumes/3`; document the current mounting order of static files vs API routes

- [X] T029 [US5] Add SPA fallback in `backend/src/persona/server.py` — added `SPAStaticFiles` subclass that overrides `get_response` to catch Starlette 404s and fall back to `index.html`; API/MCP/health routes registered before the mount take priority

- [X] T030 [US5] Update integration test in `backend/tests/integration/test_static_serving.py` — renamed 404 test to `test_spa_route_serves_index_html`; asserts `/resumes`, `/resumes/3`, `/applications/5`, `/connect` return 200 HTML; existing tests verify API routes remain unaffected

- [X] T031 [US5] Update `specs/012-client-side-routing/quickstart.md` — expanded verification step 4 (Refresh) with dev vs Docker instructions

**Checkpoint**: Page refresh and direct URL access work in all environments — dev (Vite handles fallback), Docker (backend catch-all serves index.html)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — section-level routing
- **US2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1 (but logically benefits from US1 being done first since it verifies nav works)
- **US3 (Phase 5)**: Depends on US2 (breadcrumbs go on detail views created in US2)
- **US4 (Phase 6)**: Depends on Phase 2 — can run in parallel with US1/US2
- **Polish (Phase 7)**: Depends on all user stories being complete
- **US5 (Phase 8)**: Independent of US1–US4 (backend-only change); can run in parallel with any phase after Phase 1

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — no dependencies on other stories
- **US2 (P1)**: After Phase 2 — independent of US1 (though US1 validates nav first)
- **US3 (P2)**: After US2 — breadcrumbs are rendered in detail view components modified by US2
- **US4 (P2)**: After Phase 2 — independent of US1/US2/US3
- **US5 (P1)**: Independent — backend change; can be done at any point once the feature branch exists

### Parallel Opportunities

- T008, T009, T010, T011, T012, T013, T014, T015, T016a can all run in parallel (different files)
- T017, T018 can run in parallel
- T024, T025, T025a can run in parallel
- T028, T029, T030, T031 (US5) can run in parallel with any frontend US1–US4 work
- US1 and US4 can be worked on simultaneously
- US2 can start as soon as Phase 2 completes

---

## Parallel Example: User Story 2

```bash
# Launch all list view refactors and NotFound component in parallel:
Task T008: "Create NotFound component at frontend/src/components/NotFound.tsx"
Task T009: "Create NotFound styles at frontend/src/components/NotFound.module.css"
Task T010: "Refactor ResumeListView — replace callback with Link"
Task T012: "Refactor ApplicationListView — replace callback with Link"
Task T014: "Refactor AccomplishmentListView — replace callback with Link"

# Then detail views in parallel (depend on NotFound from T008):
Task T011: "Refactor ResumeDetailView — useParams + NotFound"
Task T013: "Refactor ApplicationDetailView — useParams + NotFound"
Task T015: "Refactor AccomplishmentDetailView — useParams + NotFound"
```

## Parallel Example: User Story 5 (alongside any frontend story)

```bash
# US5 is backend-only — run it fully in parallel with any frontend story:
Task T028: "Audit StaticFiles configuration in backend/src/persona/server.py"
Task T029: "Add SPA catch-all route in backend/src/persona/api/routes.py"
Task T030: "Write integration test for SPA fallback in backend/tests/integration/"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 5)

1. Complete Phase 1: Setup (install react-router)
2. Complete Phase 2: Foundational (rewire App.tsx + Navigation.tsx)
3. Complete Phase 3: US1 — section-level URL routing
4. Complete Phase 4: US2 — deep links to detail views
5. Complete Phase 8: US5 — backend SPA fallback (can run in parallel with US1/US2)
6. **STOP and VALIDATE**: All core routing works — URLs, back button, refresh (including Docker), bookmarks
7. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Router wired up
2. US1 → Section nav via URLs (MVP-1)
3. US2 → Deep links work (MVP-2 — primary user value)
4. US5 → Page refresh / direct URL access works in production (MVP-3 — deployment requirement)
5. US3 → Breadcrumbs added (enhancement)
6. US4 → Auth redirect integration (hardening)
7. Polish → Type cleanup, test fixes, full validation
