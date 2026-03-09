# Feature Specification: Client-Side Routing with Deep Links

**Feature Branch**: `012-client-side-routing`
**Created**: 2026-03-06
**Updated**: 2026-03-08
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - URL-Based Navigation Between Sections (Priority: P1)

A user navigates between the four main sections of the app (Resumes, Applications, Accomplishments, Connect) using the top navigation. The browser URL updates to reflect the active section, the browser's back and forward buttons work as expected, and refreshing the page keeps the user on the same section.

**Why this priority**: Core navigation is the foundation of the routing feature. Without it, no other routing behavior is possible. P1 because all other stories depend on working section-level routing.

**Independent Test**: Can be fully tested by clicking between nav links, checking the URL, pressing the browser back button, and pressing F5 — delivers a working navigation experience with shareable, bookmarkable section URLs.

**Acceptance Scenarios**:

1. **Given** the user is on the Resumes section, **When** they click "Applications" in the navigation, **Then** the URL changes to `/applications`, the Applications view renders, and no full page reload occurs.
2. **Given** the user has navigated from Resumes to Applications, **When** they press the browser's back button, **Then** the URL changes to `/resumes` and the Resumes view renders.
3. **Given** the user is on `/applications`, **When** they press F5 (refresh), **Then** the page loads and the Applications view is shown — no 404 error.
4. **Given** the user navigates to `/`, **When** the app loads, **Then** they are redirected to `/resumes`.
5. **Given** the user navigates to an unknown path (e.g., `/foo`), **When** the app loads, **Then** they are redirected to `/resumes`.

---

### User Story 2 - Deep Links to Detail Views (Priority: P1)

A user navigates to a specific item's detail view. The URL uniquely identifies that item (e.g., `/resumes/3`). The user can copy this URL, open it in a new tab, share it with a colleague, or bookmark it — and it loads the same item every time without requiring navigation through the list.

**Why this priority**: This is the primary value of client-side routing for this app. Users need to share links to specific resumes, applications, or accomplishments.

**Independent Test**: Navigate to a detail view, copy the URL, open it in a new tab — the same item loads. Visit `/resumes/999` (non-existent) — a friendly not-found message appears. Visit `/resumes/abc` (invalid ID) — redirects to the Resumes list.

**Acceptance Scenarios**:

1. **Given** the user clicks a resume in the list, **When** the detail view opens, **Then** the URL is `/resumes/{id}` where `{id}` is the resume's ID.
2. **Given** a URL `/resumes/3`, **When** the user opens it in a new browser tab, **Then** resume 3 loads and is displayed.
3. **Given** a URL `/resumes/999` (non-existent ID), **When** the page loads, **Then** a user-friendly "not found" message is shown with a link back to the Resumes list.
4. **Given** a URL `/resumes/abc` (non-numeric ID), **When** the page loads, **Then** the user is redirected to `/resumes`.

---

### User Story 3 - Breadcrumb Navigation (Priority: P2)

A user is viewing a detail view (e.g., Resume "Full-Stack Engineer v3"). The detail view displays a breadcrumb trail showing their location in the hierarchy (e.g., "Resumes > Full-Stack Engineer v3"). Clicking a breadcrumb segment navigates them to that level.

**Why this priority**: Breadcrumbs improve orientation and navigation within the app. P2 because the app is functional without them — they enhance the experience.

**Independent Test**: Navigate to any detail view — breadcrumbs appear with the section name as a clickable link and the item name as plain text. Clicking the section name navigates back to the list.

**Acceptance Scenarios**:

1. **Given** the user is viewing resume "Full-Stack Engineer v3", **When** the detail view renders, **Then** a breadcrumb shows "Resumes > Full-Stack Engineer v3" where "Resumes" is a clickable link.
2. **Given** the breadcrumb is visible, **When** the user clicks "Resumes", **Then** they are navigated to `/resumes`.
3. **Given** the user is on a list view (e.g., `/resumes`), **When** the page renders, **Then** no breadcrumb is displayed.

---

### User Story 4 - Authenticated Route Protection (Priority: P2)

An unauthenticated user visits any app URL (including a deep link like `/resumes/3`). They see the sign-in page rather than app content. After signing in, they are redirected to the URL they originally requested.

**Why this priority**: All routes must be protected. Deep link redirect after sign-in is a critical UX detail that ensures users do not lose their intended destination.

**Independent Test**: Sign out, visit `/applications/5` directly, sign in — the app lands on `/applications/5`.

**Acceptance Scenarios**:

1. **Given** the user is signed out, **When** they visit `/resumes/1`, **Then** they see the sign-in page, not the resume detail.
2. **Given** the user is signed out and visits `/applications/5`, **When** they sign in, **Then** they are redirected to `/applications/5`.
3. **Given** the user is signed in, **When** they visit any valid route directly, **Then** the route renders without being redirected to sign-in.

---

### User Story 5 - Direct URL Loading Without 404 (Priority: P1)

A user loads any application URL directly — by typing it in the address bar, refreshing the page (F5), clicking a bookmark, or opening a shared link. The application loads correctly, showing the expected view. They do not see a 404 error page from the server.

**Why this priority**: Without this, every other routing story breaks in non-dev environments. If the server returns a 404 for direct URL access to `/resumes/3`, all deep linking, bookmarking, and page refresh behavior is broken. This is a foundational requirement for a working SPA deployment.

**Independent Test**: With the application running (in any environment — local dev, Docker, or production), navigate to `/accomplishments/2`, then press F5. The accomplishment detail view loads — no 404 or "Not Found" error from the server.

**Acceptance Scenarios**:

1. **Given** the app is running, **When** a user types `/resumes` directly into the address bar and presses Enter, **Then** the Resumes list view loads — not a 404.
2. **Given** the app is running, **When** a user refreshes the page on `/applications/5`, **Then** the application detail view loads — not a 404.
3. **Given** the app is running, **When** a user opens a bookmarked URL `/accomplishments/2`, **Then** the accomplishment detail view loads — not a 404.
4. **Given** the app is running in production (Docker), **When** a user accesses any route under `/resumes`, `/applications`, `/accomplishments`, or `/connect`, **Then** the app loads correctly — the server does not return a 404 for these paths.
5. **Given** a URL that is a valid API endpoint (e.g., `/api/...`), **When** accessed directly, **Then** the API responds normally — the fallback must not intercept API routes.

---

### Edge Cases

- What happens when a numeric ID is provided but the entity does not exist? → Show a user-friendly not-found message with a link back to the section list.
- What happens when a non-numeric ID is in the URL (e.g., `/resumes/abc`)? → Redirect to the section list (`/resumes`).
- What happens when an unknown top-level path is visited (e.g., `/settings`)? → Redirect to `/resumes`.
- What happens when a user refreshes mid-session in Docker/production? → The server serves the app; the client-side router handles the route — no 404.
- What happens when a user accesses `/api/...` routes directly? → These are handled by the backend API, not the client-side router or fallback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST use URL-based routing so that each view has a unique, stable URL reflecting the user's current location.
- **FR-002**: Each top-level section (Resumes, Applications, Accomplishments, Connect) MUST have a dedicated URL path (`/resumes`, `/applications`, `/accomplishments`, `/connect`).
- **FR-003**: Each detail view MUST have a unique URL that includes the item's identifier (e.g., `/resumes/3`, `/applications/7`).
- **FR-004**: The root path (`/`) MUST redirect to `/resumes`.
- **FR-005**: Unknown paths MUST redirect to `/resumes`.
- **FR-006**: Route ID parameters MUST be validated as positive integers; non-numeric or non-positive IDs MUST redirect to the section list.
- **FR-007**: Valid numeric IDs that do not correspond to an existing entity MUST display a user-friendly "not found" message with a link back to the section list.
- **FR-008**: The server MUST serve the application shell (index page) for any URL that is not an API route, health check, or static asset, so that the client-side router can render the correct view when a URL is accessed directly.
- **FR-009**: Detail views MUST display breadcrumb navigation showing the current item's location within its section hierarchy (e.g., "Resumes > Full-Stack Engineer v3").
- **FR-010**: All application routes MUST be accessible only to authenticated users; unauthenticated users MUST see the sign-in page for any route.
- **FR-011**: After signing in, the user MUST be redirected to the URL they originally requested.
- **FR-012**: Navigation between sections MUST use the browser's history API so that the browser back and forward buttons work as expected.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clicking any navigation link updates the browser URL and renders the correct view without a full page reload.
- **SC-002**: Copying a detail view URL and opening it in a new browser tab loads the same item correctly.
- **SC-003**: The browser's back and forward buttons navigate between previously visited views correctly.
- **SC-004**: Pressing F5 (page refresh) on any view — including detail views — keeps the user on the same view with the same content loaded. No 404 errors appear.
- **SC-005**: Bookmarking any URL and reopening it loads the correct view.
- **SC-006**: All 8 verification scenarios in the quickstart checklist (section nav, deep links, back button, refresh, bookmarks, auth redirect, invalid routes, invalid IDs) pass in all deployment environments (dev, Docker).
- **SC-007**: Unauthenticated users visiting any deep link are shown the sign-in page and, upon signing in, land on the originally requested URL.
- **SC-008**: The server never returns a 404 for any valid app route accessed directly; only API routes and static assets are handled by their respective handlers.

## Assumptions

- The backend server (in all environments — local dev, Docker, production) is responsible for ensuring that non-API, non-asset requests are routed to the application shell. This assumption was initially taken as a given; this spec formalizes it as a testable requirement (FR-008).
- The Vite dev server handles HTML5 history API fallback automatically for local development.
- In production/Docker, the server serving static files must be explicitly configured to fall back to `index.html` for unknown paths, unless the framework handles this by default.
- No backend data model changes are required for this feature.
- All app routes require authentication; there are no public app routes.
