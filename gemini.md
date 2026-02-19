# personal-mcp

Persona MCP Server — a Python MCP server for resume/personal data, installable via `uvx`.

## Constitution

All project principles, technology constraints, packaging rules, development workflow, and governance are defined in [`.specify/memory/constitution.md`](.specify/memory/constitution.md). That document is authoritative — read it before making changes.

## Quick Reference

```bash
# Root commands (orchestrates both frontend and backend)
make check      # lint + typecheck + test (both frontend and backend)
make build      # build frontend then backend
make run        # docker compose up --build
make run-local  # build frontend, then run backend locally
make test       # test both frontend and backend
make lint       # lint both frontend and backend
make format     # auto-format both frontend and backend

# Backend-specific (from backend/ directory)
cd backend
make check      # lint + typecheck + test
make test       # uv run pytest
make lint       # ruff check + format check
make run        # uv run persona (HTTP server)
make format     # auto-format with ruff

# Frontend-specific (from frontend/ directory)
cd frontend
make check      # lint + test
make build      # npm run build (Vite production build)
make run        # npm run dev (Vite dev server with HMR)
make lint       # npm run lint (ESLint)
make test       # npm run test (Vitest)
```

## Project Layout

```
frontend/                 # React SPA
  src/
    components/           # React components (view + edit modes)
    services/             # API client (fetch wrapper)
    types/                # TypeScript type definitions
    __tests__/            # Vitest component tests
    App.tsx               # Root component
    main.tsx              # Entry point
    index.css             # Global styles
  public/                 # Static assets
  dist/                   # Build output (served by backend)
  index.html              # HTML template
  package.json            # Node.js dependencies
  tsconfig.json           # TypeScript config
  vite.config.ts          # Vite build + proxy config
  eslint.config.js        # ESLint config
  Makefile                # Frontend build targets
backend/                  # Python FastAPI + MCP server
  src/persona/            # Python package
    server.py             # FastAPI + MCP server entrypoint
    models.py             # Pydantic data models
    config.py             # Configuration
    database.py           # SQLite operations
    db.py                 # DBConnection protocol
    resume_service.py     # Shared business logic
    api/                  # REST API routes
      routes.py           # FastAPI route handlers
    tools/                # MCP tool handlers (read.py, write.py)
  tests/
    unit/                 # Unit tests
    contract/             # MCP + REST API contract tests
    integration/          # Integration tests (incl. cross-interface, static serving)
  pyproject.toml          # Python package config
  uv.lock                 # Locked dependencies
  Makefile                # Backend build targets
Makefile                  # Root orchestrator
Dockerfile                # Multi-stage Docker build (Node.js + Python)
docker-compose.yml        # Docker Compose configuration
specs/                    # Feature specifications
.specify/                 # Spec-kit configuration
.github/                  # GitHub Actions CI
```

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## Active Technologies

### Backend
- Python 3.11+ with type hints and Pydantic validation
- FastMCP >=2.3.0 for MCP server (streamable-http + stdio)
- FastAPI >=0.100.0 for REST API + static file serving
- uvicorn >=0.20.0 for ASGI HTTP server
- SQLite via stdlib `sqlite3` with `DBConnection` protocol (Schema v3)
- `uv` for dependency management and packaging
- pytest for testing (unit, contract, integration)
- ruff for linting and formatting
- pyright for type checking
- python-jose, svix (Authentication logic)

### Frontend
- React 18 with TypeScript 5.x
- Vite 6 for build tooling and dev server
- Clerk (Auth SDK)
- Vitest 2 with React Testing Library for component tests
- ESLint 9 with typescript-eslint for linting
- CSS Modules for component styling

### Infrastructure
- Docker + Docker Compose for containerized deployment (multi-stage build)
- GNU Make for build orchestration (root + per-directory Makefiles)


## Recent Changes
- feature/002-ci-pipeline: Added Python 3.11 (minimum supported per pyproject.toml) + GitHub Actions, `astral-sh/setup-uv` action
