# Quickstart: Resume Web User Interface

**Branch**: `feat-005-user-interface` | **Date**: 2026-02-12

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- `uv` (Python package manager)
- Docker and Docker Compose (for containerized runs)
- GNU Make

## Project Structure (after restructure)

```
persona/
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/           # API client
│   │   ├── types/              # TypeScript type definitions
│   │   ├── App.tsx             # Root component
│   │   └── main.tsx            # Entry point
│   ├── public/                 # Static assets
│   ├── index.html              # HTML template
│   ├── package.json            # Node.js dependencies
│   ├── tsconfig.json           # TypeScript config
│   ├── vite.config.ts          # Vite build config
│   └── Makefile                # Frontend targets
├── backend/                    # Python FastAPI + MCP server
│   ├── src/persona/            # Python package
│   │   ├── server.py           # FastAPI + MCP entrypoint
│   │   ├── models.py           # Pydantic models
│   │   ├── database.py         # SQLite operations
│   │   ├── config.py           # Configuration
│   │   ├── resume_service.py   # Business logic
│   │   ├── api/routes.py       # REST API routes
│   │   └── tools/              # MCP tools
│   ├── tests/                  # Python tests
│   ├── pyproject.toml          # Python package config
│   ├── uv.lock                 # Locked dependencies
│   └── Makefile                # Backend targets
├── Makefile                    # Root orchestrator
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Container orchestration
├── CLAUDE.md                   # AI assistant instructions
├── README.md                   # User documentation
└── specs/                      # Feature specifications
```

## Development

### Full Build (from root)

```bash
make build    # Builds frontend (npm) then backend (Python deps)
make run      # Starts via Docker Compose
make check    # Lint + test both frontend and backend
```

### Frontend Only

```bash
cd frontend
make build    # npm run build (production)
make run      # npm run dev (dev server with HMR)
make lint     # npm run lint (ESLint)
make test     # npm run test (Vitest)
make check    # lint + test
```

### Backend Only

```bash
cd backend
make build    # Install Python dependencies
make run      # uv run persona (start HTTP server)
make lint     # ruff check + format check
make test     # uv run pytest
make check    # lint + typecheck + test
```

### Docker

```bash
# From root
make run              # docker compose up --build
# OR
docker compose up --build
```

## Key Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `PERSONA_PORT` | 8000 | HTTP server port |
| `PERSONA_DATA_DIR` | ~/.persona | Database location |
| `LOG_LEVEL` | INFO | Logging verbosity |

## URL Map (running locally)

| Path | What |
|------|------|
| `http://localhost:8000/` | React SPA (frontend) |
| `http://localhost:8000/api/resume` | REST API |
| `http://localhost:8000/mcp` | MCP endpoint |
| `http://localhost:8000/health` | Health check |

## Frontend Development with Backend

For frontend development with live reload against the running backend:

1. Start the backend: `cd backend && make run` (runs on port 8000)
2. Start the frontend dev server: `cd frontend && make run` (runs on port 5173 with proxy to 8000)
3. Access the dev server at `http://localhost:5173/`

The Vite dev server proxies `/api/*` and `/health` requests to the backend, simulating production same-origin behavior.

## Testing

```bash
# Run everything
make check

# Frontend tests
cd frontend && make test

# Backend tests (no frontend build required)
cd backend && make test

# Individual test runs
cd backend && uv run pytest tests/unit/
cd backend && uv run pytest tests/contract/
cd backend && uv run pytest tests/integration/
```
