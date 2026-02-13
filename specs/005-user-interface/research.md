# Research: Resume Web User Interface

**Branch**: `feat-005-user-interface` | **Date**: 2026-02-12

## R1: React Build Toolchain

**Decision**: Vite with React + TypeScript template

**Rationale**: Vite is the current standard for React projects. It provides near-instant dev server startup with HMR, optimized production builds via Rollup, and first-class TypeScript support. Create React App is deprecated. Next.js is server-oriented and overkill for a static SPA.

**Alternatives considered**:
- Create React App (CRA): Deprecated, slow builds, no longer maintained
- Next.js: Server-side rendering framework; adds unnecessary complexity for a single-page static app served by an existing backend
- Parcel: Viable but smaller ecosystem and less community adoption than Vite

## R2: Frontend State Management

**Decision**: React hooks (useState, useEffect) with a custom `useApi` hook

**Rationale**: The app has a flat data model (one resume with five sections). There is no complex state graph, no deeply nested components sharing state, and no real-time collaboration. React's built-in hooks are sufficient and avoid adding dependencies.

**Alternatives considered**:
- Redux / Zustand / Jotai: Overkill for a single-resource CRUD app
- React Query (TanStack Query): Good for caching/refetching patterns but adds a dependency for a single-user app with minimal data. Could be revisited if requirements grow.

## R3: HTTP Client

**Decision**: Browser `fetch` API with a thin wrapper module

**Rationale**: The app makes simple REST calls to a same-origin API. The native `fetch` API handles this without any dependency. A thin wrapper module centralizes base URL, error handling, and JSON parsing.

**Alternatives considered**:
- Axios: Adds a dependency for marginal convenience (interceptors, automatic JSON). Not justified for this scope.
- ky: Lightweight fetch wrapper, but still an extra dependency.

## R4: CSS / Styling Approach

**Decision**: CSS Modules (built into Vite)

**Rationale**: CSS Modules provide locally-scoped styles with zero additional dependencies. Vite supports them natively via `*.module.css` file naming. This avoids CSS-in-JS runtime cost and keeps the build simple.

**Alternatives considered**:
- Tailwind CSS: Popular utility-first framework but adds build toolchain complexity and a learning curve for a small app
- styled-components / Emotion: CSS-in-JS adds runtime overhead and a dependency
- Plain CSS: Works but risks class name collisions as component count grows

## R5: Frontend Testing

**Decision**: Vitest with React Testing Library

**Rationale**: Vitest is the natural testing companion for Vite projects — same config, same transforms, fast execution. React Testing Library encourages testing user behavior rather than implementation details.

**Alternatives considered**:
- Jest: Requires separate configuration from Vite; Vitest is a drop-in replacement with better Vite integration
- Cypress component testing: Heavier, better suited for E2E tests than unit/component tests

## R6: Serving Static Frontend from FastAPI

**Decision**: FastAPI `StaticFiles` mount at `/` with route priority ordering

**Rationale**: FastAPI's `StaticFiles` (from Starlette) can serve the built frontend assets. API routes (`/api/*`), MCP (`/mcp`), and health (`/health`) are registered first and take priority. The static mount is registered last as a catch-all, serving `index.html` for the root path and any unmatched paths (SPA fallback).

**Implementation approach**:
1. Register API router, MCP mount, and health endpoint first (these have explicit paths)
2. Mount `StaticFiles` at `/` pointing to the frontend `dist/` directory with `html=True` (serves `index.html` for `/`)
3. The `html=True` option handles SPA fallback — unmatched paths serve `index.html`
4. If the frontend dist directory doesn't exist, skip the mount and log a warning (backend still starts for dev/test)

**Alternatives considered**:
- Nginx reverse proxy: Adds operational complexity (separate process, config) for a single-user tool
- Separate container for frontend: Eliminated per spec clarification — single container
- FastAPI catch-all route returning FileResponse: Works but `StaticFiles` is the Starlette-idiomatic approach

## R7: Directory Restructure Strategy

**Decision**: Move existing source into `backend/` subdirectory, create `frontend/` alongside

**Rationale**: The spec requires `frontend/` and `backend/` at the repo root. The existing code under `src/backend/` and `tests/` moves into `backend/`. This keeps Python package imports working with minimal changes by preserving the `src/backend/` structure inside `backend/src/backend/`.

**Migration plan**:
```
BEFORE:                          AFTER:
src/backend/                     backend/src/persona/    (package renamed)
tests/                           backend/tests/
Makefile                         backend/Makefile (backend-specific)
pyproject.toml                   backend/pyproject.toml
Dockerfile                       Dockerfile (root, multi-stage)
docker-compose.yml               docker-compose.yml (root)
                                 frontend/          (new)
                                 frontend/Makefile   (new)
                                 Makefile            (root orchestrator)
```

**Package rename** (`backend` → `persona`):
- The Python package is renamed from `backend` to `persona` to avoid the redundant `backend/src/backend/` path
- All `import backend.*` statements updated to `import persona.*` across source and tests
- `pyproject.toml` entry point updated: `persona = "persona.server:main"`
- `[tool.hatch.build.targets.wheel] packages` updated to `["src/persona"]`
- Dockerfile `CMD` updated: `python -m persona.server`

**Key considerations**:
- `pyproject.toml` moves to `backend/` since it defines the Python package
- `uv.lock` moves to `backend/` alongside `pyproject.toml`
- Root `Dockerfile` does a multi-stage build: Node.js stage builds frontend, Python stage runs backend with frontend assets copied in
- Root `docker-compose.yml` stays at root, builds from root Dockerfile
- `CLAUDE.md` stays at root but paths updated
- `.github/` stays at root
- `specs/` and `.specify/` stay at root (project-level, not backend-specific)

## R8: Makefile Structure

**Decision**: Three Makefiles with targets `build`, `run`, `lint`, `test`, `check`

**Root Makefile** (orchestrator):
- `build`: builds frontend then backend (in order)
- `run`: runs the full application (docker compose up or local)
- `lint`: lints both frontend and backend
- `test`: tests both frontend and backend
- `check`: lint + test for both

**Frontend Makefile** (`frontend/Makefile`):
- `build`: `npm run build` (Vite production build)
- `run`: `npm run dev` (Vite dev server)
- `lint`: `npm run lint` (ESLint)
- `test`: `npm run test` (Vitest)
- `check`: lint + test

**Backend Makefile** (`backend/Makefile`):
- `build`: no-op or Python package build (the backend doesn't need a compile step)
- `run`: `uv run persona` (start HTTP server locally)
- `lint`: `uv run ruff check . && uv run ruff format --check .`
- `test`: `uv run pytest`
- `check`: lint + typecheck + test

**Rationale**: Matches the constitution's requirement for `make check` as the pre-commit gate. Each component can be developed independently. The root Makefile ensures proper build order (frontend first, since backend serves frontend assets).

## R9: Docker Multi-Stage Build

**Decision**: Single Dockerfile at repo root with three stages

**Stages**:
1. **frontend-builder**: Node.js image, installs npm deps, runs `npm run build`, outputs `frontend/dist/`
2. **backend-builder**: Python image, installs `uv`, syncs Python deps, creates `.venv`
3. **runtime**: Python slim image, copies `.venv` from backend-builder, copies `backend/src/` and `frontend/dist/` into the image

**Rationale**: Single Dockerfile produces one container image. Multi-stage keeps the final image small (no Node.js, no build tools). The frontend assets are just static files copied into the backend's serving directory.
