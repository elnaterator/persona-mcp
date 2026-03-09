# Route Contracts: Client-Side Routing

**Feature**: 012-client-side-routing
**Date**: 2026-03-06

## Overview

No new API endpoints. This feature adds client-side URL routes only. The backend already serves the SPA correctly for all paths.

## Client-Side Route Definitions

```text
<BrowserRouter>
  <ClerkProvider>
    <SignedOut>
      <LandingPage />          # Shown for all routes when unauthenticated
    </SignedOut>
    <SignedIn>
      <Layout>                 # Header with Navigation + UserMenu
        <Routes>
          <Route path="/" element={<Navigate to="/resumes" replace />} />
          <Route path="/resumes" element={<ResumeListView />} />
          <Route path="/resumes/:id" element={<ResumeDetailView />} />
          <Route path="/applications" element={<ApplicationListView />} />
          <Route path="/applications/:id" element={<ApplicationDetailView />} />
          <Route path="/accomplishments" element={<AccomplishmentListView />} />
          <Route path="/accomplishments/:id" element={<AccomplishmentDetailView />} />
          <Route path="/connect" element={<ConnectView />} />
          <Route path="*" element={<Navigate to="/resumes" replace />} />
        </Routes>
      </Layout>
    </SignedIn>
  </ClerkProvider>
</BrowserRouter>
```

## Navigation Contracts

### Section Navigation (NavLink)

| Nav Item | Target URL | Active When |
|----------|-----------|-------------|
| Resumes | `/resumes` | Path starts with `/resumes` |
| Applications | `/applications` | Path starts with `/applications` |
| Accomplishments | `/accomplishments` | Path starts with `/accomplishments` |
| Connect | `/connect` | Path equals `/connect` |

### Detail Navigation (Link)

| From | Action | Target URL |
|------|--------|-----------|
| Resume list item | Click item | `/resumes/{id}` |
| Resume detail | Click back / breadcrumb | `/resumes` |
| Application list item | Click item | `/applications/{id}` |
| Application detail | Click back / breadcrumb | `/applications` |
| Accomplishment list item | Click item | `/accomplishments/{id}` |
| Accomplishment detail | Click back / breadcrumb | `/accomplishments` |

## Redirect Contracts

| Condition | From | To | Method |
|-----------|------|-----|--------|
| Root visit | `/` | `/resumes` | Replace (no history entry) |
| Unknown route | `/anything` | `/resumes` | Replace |
| Invalid ID format | `/resumes/abc` | `/resumes` | Replace |
| Non-existent ID | `/resumes/999` | Inline NotFound | N/A (stays on URL) |

## Auth Integration Contract

| Condition | Behavior |
|-----------|----------|
| Unauthenticated visit to any route | Show LandingPage with sign-in |
| Post sign-in redirect | Navigate to originally requested URL |
| Authenticated visit to `/` | Redirect to `/resumes` |
