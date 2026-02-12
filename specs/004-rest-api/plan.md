# Implementation Plan: REST API & Remote MCP Server with Docker Support

**Branch**: `feat-004-rest-api` | **Date**: 2026-02-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-rest-api/spec.md`

## Summary

Add a REST API for CRUD operations on resume data, serve MCP via streamable-http as a remote MCP server, and package everything in Docker Compose. The backend source code moves from `src/persona/` to `src/backend/`. A new `ResumeService` class encapsulates all resume operations with a generic `DBConnection` protocol type (PEP 249-based) to prepare for a future PostgreSQL migration. FastAPI serves the REST API, FastMCP mounts at `/mcp` for streamable-http MCP, and a `--stdio` flag preserves backward compatibility with local MCP clients.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `fastmcp>=2.3.0`, `fastapi>=0.100.0`, `uvicorn>=0.20.0` (replaces `mcp>=1.0.0`)
**Storage**: SQLite via stdlib `sqlite3` (existing, unchanged) with `DBConnection` protocol for future DB swaps
**Testing**: `pytest` with `pytest-asyncio`
**Target Platform**: Linux server (Docker), macOS/Linux for local dev
**Project Type**: Single backend application with Docker containerization
**Performance Goals**: App responds within 5 seconds of start (SC-006)
**Constraints**: Single process serving both REST and MCP; shared DB connection
**Scale/Scope**: Personal resume server — single user, low concurrency

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | MCP tools remain exposed via streamable-http transport; all lifecycle methods handled by FastMCP |
| II. Single-Package Distribution via uvx | PASS | `uvx persona` still works; entry point updated to `backend.server:main`; `--stdio` flag for backward compat |
| III. Test-Driven Development | PASS | TDD workflow maintained; tests written before implementation |
| IV. Minimal Dependencies | PASS | 3 new deps justified: `fastmcp` (MCP+HTTP), `fastapi` (REST), `uvicorn` (ASGI server). See R-009 |
| V. Explicit Error Handling | PASS | REST API returns structured JSON errors; MCP error handling unchanged |
| Makefile targets | PASS | Mandatory targets (`run`, `test`, `lint`, `check`) preserved; `run` updated to Docker Compose; `run-local` added |
| Conventional commits | PASS | Will follow `feat:`, `refactor:`, `test:`, `docs:` prefixes |
| README updates | PASS | Task included for README update |

## Project Structure

### Documentation (this feature)

```text
specs/004-rest-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── openapi.yaml     # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/backend/                    # Renamed from src/persona/
├── __init__.py                 # Package version
├── db.py                       # NEW: DBConnection protocol
├── database.py                 # SQLite operations (uses DBConnection)
├── migrations.py               # Schema migrations (unchanged logic)
├── models.py                   # Pydantic data models (unchanged)
├── config.py                   # Configuration (add PERSONA_PORT, CORS)
├── resume_service.py           # NEW: ResumeService class
├── server.py                   # Unified entry point (FastAPI + MCP + --stdio)
├── api/                        # NEW: REST API routes
│   ├── __init__.py
│   └── routes.py               # FastAPI route handlers
└── tools/                      # MCP tool handlers (updated to use ResumeService)
    ├── __init__.py
    ├── read.py
    └── write.py

tests/
├── conftest.py                 # Updated fixtures (ResumeService, DBConnection)
├── unit/
│   ├── test_config.py          # Updated for new config vars
│   ├── test_database.py        # Updated imports
│   ├── test_migrations.py      # Updated imports
│   ├── test_models.py          # Updated imports
│   └── test_resume_service.py  # NEW: ResumeService unit tests
├── contract/
│   ├── test_read_tools.py      # Updated to use ResumeService
│   ├── test_write_tools.py     # Updated to use ResumeService
│   └── test_rest_api.py        # NEW: REST API contract tests
└── integration/
    ├── test_server.py          # Updated for HTTP server mode
    └── test_cross_interface.py # NEW: REST↔MCP shared state tests

Dockerfile                      # NEW: Multi-stage Python build
docker-compose.yml              # NEW: Single persona service
.dockerignore                   # NEW: Exclude unnecessary files
```

**Structure Decision**: Single backend project in `src/backend/` with a new `api/` sub-package for REST routes. The existing `tools/` sub-package for MCP handlers is preserved. A new `resume_service.py` module sits at the package root as the shared business logic layer used by both `api/routes.py` and `tools/*.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `DBConnection` Protocol | User requires DB-agnostic typing for future PostgreSQL swap | Using `sqlite3.Connection` directly would create tight coupling that requires touching every file when switching DBs |
| `ResumeService` class | User requires constructor injection pattern to avoid passing connection per-call | Function-based approach already existed but user explicitly wants class-based for cleaner API |
| Package rename `persona` → `backend` | User requires `src/backend/` directory structure | Keeping `src/persona/` was rejected by user |
