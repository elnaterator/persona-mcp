# personal-mcp

Persona MCP Server — a Python MCP server for resume/personal data, installable via `uvx`.

## Constitution

All project principles, technology constraints, packaging rules, development workflow, and governance are defined in [`.specify/memory/constitution.md`](.specify/memory/constitution.md). That document is authoritative — read it before making changes.

## Quick Reference

```bash
make check    # lint + typecheck + test (run before committing)
make test     # uv run pytest
make lint     # ruff check + format check
make run      # uv run persona
make format   # auto-format with ruff
```

## Project Layout

```
src/backend/          # main package (renamed from persona)
  server.py           # FastAPI + MCP server entrypoint
  models.py           # Pydantic data models
  config.py           # configuration
  database.py         # SQLite operations
  db.py               # DBConnection protocol
  resume_service.py   # shared business logic
  api/                # REST API routes
    routes.py         # FastAPI route handlers
  tools/              # MCP tool handlers (read.py, write.py)
tests/
  unit/               # unit tests
  contract/           # MCP + REST API contract tests
  integration/        # integration tests (incl. cross-interface)
docker-compose.yml    # Docker Compose configuration
Dockerfile            # Multi-stage Docker build
```

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## Active Technologies
- Python 3.11+ with type hints and Pydantic validation
- FastMCP >=2.3.0 for MCP server (streamable-http + stdio)
- FastAPI >=0.100.0 for REST API
- uvicorn >=0.20.0 for ASGI HTTP server
- SQLite via stdlib `sqlite3` with `DBConnection` protocol for DB-agnostic code
- Docker + Docker Compose for containerized deployment
- `uv` for dependency management and packaging
- pytest for testing (unit, contract, integration)
- ruff for linting and formatting
- pyright for type checking
- Python 3.11+ (backend), TypeScript 5.x (frontend) + FastAPI, FastMCP, uvicorn (backend); React 18, Vite 5 (frontend) (feat-005-user-interface)
- SQLite via stdlib `sqlite3` (existing, unchanged) (feat-005-user-interface)
- Python 3.11+ (backend), TypeScript 5.x (frontend) + FastMCP >=2.3.0, FastAPI >=0.100.0, React 18, Vite 6 (006-job-applications)
- SQLite via stdlib `sqlite3` (schema migration v1 → v2) (006-job-applications)
- SQLite via stdlib sqlite3 with DBConnection protocol (006-job-applications)
- Python 3.11+ (backend), TypeScript 5.x (frontend) + FastMCP >=2.3.0, FastAPI >=0.100.0, React 18, Vite 6 (all existing — no new deps) (feat-007-accomplishments)
- SQLite via stdlib `sqlite3`, schema v2 → v3 migration (feat-007-accomplishments)

## Recent Changes
- feature/002-ci-pipeline: Added Python 3.11 (minimum supported per pyproject.toml) + GitHub Actions, `astral-sh/setup-uv` action
