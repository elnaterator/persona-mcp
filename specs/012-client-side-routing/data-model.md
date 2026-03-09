# Data Model: Client-Side Routing with Deep Links

**Feature**: 012-client-side-routing
**Date**: 2026-03-06

## Overview

This feature introduces no new persistent data entities. All changes are in the frontend routing layer. This document defines the routing data model (URL-to-view mapping) and component interface changes.

## Route Map

| Path | View Component | Params | Breadcrumb Label |
|------|---------------|--------|-----------------|
| `/` | Redirect → `/resumes` | — | — |
| `/resumes` | `ResumeListView` | — | — |
| `/resumes/:id` | `ResumeDetailView` | `id: number` | "Resumes > {version.label}" |
| `/applications` | `ApplicationListView` | — | — |
| `/applications/:id` | `ApplicationDetailView` | `id: number` | "Applications > {app.company} — {app.position}" |
| `/accomplishments` | `AccomplishmentListView` | — | — |
| `/accomplishments/:id` | `AccomplishmentDetailView` | `id: number` | "Accomplishments > {acc.title}" |
| `/connect` | `ConnectView` | — | — |
| `*` (catch-all) | Redirect → `/resumes` | — | — |

## Component Interface Changes

### Components Losing Props (router replaces callbacks)

**ResumeListView**:
- Remove: `onSelectResume: (id: number) => void`
- Add: Internal `<Link to={`/resumes/${id}`}>` for each item

**ResumeDetailView**:
- Remove: `onBack: () => void`
- Remove: `versionId: number` (from props)
- Add: `useParams()` to extract `id` from URL
- Add: `useNavigate()` or `<Link>` for back navigation

**ApplicationListView**:
- Remove: `onSelectApp: (id: number) => void`
- Add: Internal `<Link to={`/applications/${id}`}>` for each item

**ApplicationDetailView**:
- Remove: `onBack: () => void`
- Remove: `appId: number` (from props)
- Add: `useParams()` to extract `id` from URL
- Add: `useNavigate()` or `<Link>` for back navigation

**AccomplishmentListView**:
- Remove: `onSelectAccomplishment: (id: number) => void`
- Add: Internal `<Link to={`/accomplishments/${id}`}>` for each item

**AccomplishmentDetailView**:
- Remove: `onBack: () => void`
- Remove: `accomplishmentId: number` (from props)
- Add: `useParams()` to extract `id` from URL
- Add: `useNavigate()` or `<Link>` for back navigation

### New Components

**Breadcrumb**:
- Props: `items: { label: string; to?: string }[]`
- Renders: Clickable segments separated by " > ". Last segment is plain text (current page).
- Visibility: Only rendered on detail views.

**NotFound**:
- Props: `entityName: string; backTo: string; backLabel: string`
- Renders: "Not found" message with a link back to the list.

### Navigation Component Changes

**Navigation**:
- Remove: `onNavigate: (view: NavSection) => void`
- Keep: `activeView` derived from current route (via `useLocation()` or `NavLink` auto-active)
- Replace: `<button>` elements with `<NavLink to="/resumes">` etc.
- `NavLink` provides automatic `aria-current="page"` and active CSS class

### App Component Changes

**App**:
- Remove: `View` type, `useState<View>`, `handleNavigate`, conditional rendering
- Add: `<BrowserRouter>` wrapping `<ClerkProvider>`
- Add: `<Routes>` with route definitions inside `<SignedIn>`
- Layout route renders header (Navigation, UserMenu) + `<Outlet>` for child routes

## Validation Rules

- Route `:id` params MUST be validated as positive integers
- Non-numeric `:id` values redirect to the section list view
- Valid numeric IDs for non-existent entities show the NotFound component
