# Quickstart: Client-Side Routing with Deep Links

**Feature**: 012-client-side-routing
**Date**: 2026-03-06

## Prerequisites

- Node.js 18+ and npm installed
- Frontend dev dependencies installed (`cd frontend && npm install`)

## Setup

1. Install React Router:
   ```bash
   cd frontend
   npm install react-router
   ```

2. Start dev server:
   ```bash
   npm run dev
   ```
   Vite serves at `http://localhost:5173` with automatic history API fallback.

3. Start backend (separate terminal):
   ```bash
   cd backend
   make run
   ```

## Verification

After implementation, verify routing works:

1. **Section navigation**: Click between Resumes, Applications, Accomplishments, Connect — URL should update
2. **Deep links**: Navigate to a resume detail, copy the URL, paste in new tab — same resume should load
3. **Back button**: Navigate Resumes → resume detail → browser back — should return to Resumes list
4. **Refresh**: On any page, press F5 — should stay on the same page
   - *Dev server*: Vite handles the fallback automatically — no extra config needed.
   - *Docker/production*: Run `make run`, navigate to a detail view (e.g. `/resumes/3`), press F5 — the app reloads showing the same view, not a 404. This requires the backend SPA fallback (`SPAStaticFiles`) to be in place.
5. **Bookmarks**: Bookmark `/applications/1`, close tab, open bookmark — should load that application
6. **Auth redirect**: Sign out, visit `/resumes/1` directly, sign in — should land on `/resumes/1`
7. **Invalid routes**: Visit `/foo` — should redirect to `/resumes`
8. **Invalid IDs**: Visit `/resumes/abc` — should redirect to `/resumes`

## Running Tests

```bash
cd frontend
npm run test        # Run all tests
npm run test -- --run   # Run once (no watch)
```

## Key Files

| File | Purpose |
|------|---------|
| `src/App.tsx` | Root component with BrowserRouter + ClerkProvider |
| `src/components/Navigation.tsx` | Top nav with NavLink components |
| `src/components/Breadcrumb.tsx` | Breadcrumb navigation for detail views |
| `src/components/NotFound.tsx` | Not-found message for invalid IDs |
| `src/__tests__/components/routing.test.tsx` | Route integration tests |
