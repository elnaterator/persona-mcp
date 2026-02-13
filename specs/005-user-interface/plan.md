# Implementation Plan: Resume Web User Interface

**Branch**: `feat-005-user-interface` | **Date**: 2026-02-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-user-interface/spec.md`

## Summary

Add a React SPA frontend to the existing Persona MCP server. The frontend is served by the same FastAPI process from the root path `/`, while existing API (`/api/*`) and MCP (`/mcp`) endpoints continue functioning unchanged. The project is restructured into `frontend/` and `backend/` top-level directories with separate Makefiles, orchestrated by a root Makefile. Everything runs in a single Docker container.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, FastMCP, uvicorn (backend); React 18, Vite 5 (frontend)
**Storage**: SQLite via stdlib `sqlite3` (existing, unchanged)
**Testing**: pytest + pytest-asyncio (backend); Vitest + React Testing Library (frontend)
**Target Platform**: Docker container (Linux), local dev on macOS/Linux
**Project Type**: Web application (frontend + backend monorepo)
**Performance Goals**: Resume load <3s, edit-save feedback <2s
**Constraints**: Single container, single server process, same-origin serving
**Scale/Scope**: Single-user personal tool, 1 page, ~10 React components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | MCP endpoints unchanged at `/mcp` |
| II. Single-Package Distribution via uvx | PASS | Backend still installable via `uvx persona`; frontend assets are optional static files |
| III. Test-Driven Development | PASS | Frontend uses Vitest + RTL; backend uses pytest. TDD workflow maintained. |
| IV. Minimal Dependencies | PASS w/ NOTE | Frontend introduces Node.js ecosystem (React, Vite). Justified: frontend requires JS toolchain. Backend adds no new Python dependencies. |
| V. Explicit Error Handling | PASS | Frontend displays structured error messages from API; no unhandled exceptions exposed. |
| Makefile targets | PASS | All three Makefiles include `build`, `run`, `lint`, `test`, `check` targets per user request and constitution. |
| README updates | PASS | Will update README to reflect new project structure and frontend capability. |

**Post-Phase 1 re-check**: PASS. The frontend is a separate build artifact served as static files. It does not modify backend Python code beyond adding a `StaticFiles` mount. The `uvx` distribution path is preserved — when installed via `uvx`, the frontend simply isn't present and the server runs without it (API + MCP only).

## Project Structure

### Documentation (this feature)

```text
specs/005-user-interface/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity mapping (backend → frontend types)
├── quickstart.md        # Phase 1: development setup guide
├── contracts/           # Phase 1: API contract reference
│   └── api-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/persona/
│   ├── __init__.py
│   ├── server.py           # FastAPI + MCP + StaticFiles mount
│   ├── config.py           # Configuration (add FRONTEND_DIR)
│   ├── models.py           # Pydantic models (unchanged)
│   ├── db.py               # DBConnection protocol (unchanged)
│   ├── database.py         # SQLite CRUD (unchanged)
│   ├── migrations.py       # Schema migrations (unchanged)
│   ├── resume_service.py   # Business logic (unchanged)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py       # REST routes (unchanged)
│   └── tools/
│       ├── __init__.py
│       ├── read.py          # MCP read tools (unchanged)
│       └── write.py         # MCP write tools (unchanged)
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── contract/
│   └── integration/
├── pyproject.toml
├── uv.lock
└── Makefile                 # Backend: build, run, lint, test, check

frontend/
├── src/
│   ├── components/
│   │   ├── ResumeView.tsx             # Main resume display
│   │   ├── ContactSection.tsx         # Contact info view + edit
│   │   ├── SummarySection.tsx         # Summary view + edit
│   │   ├── ExperienceSection.tsx      # Experience list view + add/edit/delete
│   │   ├── EducationSection.tsx       # Education list view + add/edit/delete
│   │   ├── SkillsSection.tsx          # Skills list view + add/edit/delete
│   │   ├── EditableSection.tsx        # Shared edit/view toggle wrapper
│   │   ├── EntryForm.tsx              # Generic form for list entries
│   │   ├── ConfirmDialog.tsx          # Delete confirmation
│   │   ├── StatusMessage.tsx          # Success/error notifications
│   │   └── LoadingSpinner.tsx         # Loading state indicator
│   ├── services/
│   │   └── api.ts                     # API client (fetch wrapper)
│   ├── types/
│   │   └── resume.ts                  # TypeScript type definitions
│   ├── App.tsx                        # Root component
│   ├── main.tsx                       # React DOM render entry
│   └── index.css                      # Global styles
├── public/                            # Static assets (favicon, etc.)
├── index.html                         # Vite HTML template
├── package.json
├── tsconfig.json
├── vite.config.ts                     # Vite config (dev proxy to backend)
├── eslint.config.js                   # ESLint configuration
└── Makefile                           # Frontend: build, run, lint, test, check

# Root files
Makefile                     # Orchestrator: build, run, lint, test, check
Dockerfile                   # Multi-stage: Node.js build + Python runtime
docker-compose.yml           # Single service, single container
CLAUDE.md                    # Updated project instructions
README.md                    # Updated documentation
```

**Structure Decision**: Web application layout with `frontend/` and `backend/` at repo root. The existing `src/backend/` is moved to `backend/src/persona/` — renaming the Python package from `backend` to `persona` to avoid the redundant `backend/src/backend/` path and align the package name with the project name. All `import backend.*` statements are updated to `import persona.*`. `tests/` moves to `backend/tests/`. A new `frontend/` directory contains the React SPA bootstrapped with Vite.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Node.js ecosystem dependency | Frontend requires JavaScript build toolchain (React + Vite) | Server-rendered HTML would avoid Node.js but doesn't meet React SPA requirement from spec clarifications |
| Three Makefiles | User requirement: separate frontend/backend Makefiles + root orchestrator | Single Makefile would work but violates spec requirement for independent frontend/backend build commands |
| Package rename `backend` → `persona` | Avoids redundant `backend/src/backend/` path in monorepo layout | Keeping `backend` package name creates confusing double-nesting; rename aligns package name with project name |
