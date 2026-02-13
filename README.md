# Persona MCP Server

An MCP (Model Context Protocol) server that exposes personal data — starting with resume management — to AI assistants. Features a web UI, REST API, and remote MCP access over HTTP.

## Features

- **Web User Interface**: React SPA for viewing and editing resume data in a browser
- **Resume Management**: Store and query your resume data (contact, summary, experience, education, skills)
- **REST API**: Full CRUD operations via HTTP at `/api/resume` endpoints
- **Remote MCP Server**: Access MCP tools over HTTP (streamable-http transport) at `/mcp`
- **Unified Serving**: Single FastAPI server serves both the frontend SPA and backend API
- **Docker Support**: Run via Docker Compose with persistent data storage
- **SQLite Storage**: Persistent, schema-versioned database with automatic migrations
- **Type-Safe**: Full Pydantic validation (backend) and TypeScript types (frontend)

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and run
git clone <repo-url>
cd persona-mcp
make run  # Starts server on http://localhost:8000

# Or use docker compose directly
docker compose up --build
```

The server will be available at:
- **Web UI**: `http://localhost:8000/` (resume viewer/editor)
- **REST API**: `http://localhost:8000/api/resume`
- **MCP endpoint**: `http://localhost:8000/mcp`
- **Health check**: `http://localhost:8000/health`

### Option 2: Local Development

```bash
# Build frontend and run backend locally
make run-local

# Or run frontend and backend separately:

# Terminal 1: Start backend (from backend/)
cd backend
make run      # Runs on http://localhost:8000

# Terminal 2: Start frontend dev server (from frontend/)
cd frontend
make run      # Runs on http://localhost:5173 with proxy to backend

# Run backend in stdio mode (MCP only, no HTTP)
cd backend
uv run persona --stdio
```

## REST API Usage

```bash
# Get full resume
curl http://localhost:8000/api/resume

# Get a specific section
curl http://localhost:8000/api/resume/experience

# Update contact info
curl -X PUT http://localhost:8000/api/resume/contact \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Add a skill
curl -X POST http://localhost:8000/api/resume/skills/entries \
  -H "Content-Type: application/json" \
  -d '{"name": "Python", "category": "Languages"}'

# Update an entry
curl -X PUT http://localhost:8000/api/resume/skills/entries/0 \
  -H "Content-Type: application/json" \
  -d '{"name": "Python 3.11", "category": "Languages"}'

# Delete an entry
curl -X DELETE http://localhost:8000/api/resume/skills/entries/0
```

## MCP Integration

### Remote Access (HTTP) — Default

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "persona": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Local Access (stdio) — Backward Compatible

```json
{
  "mcpServers": {
    "persona": {
      "command": "uvx",
      "args": ["persona", "--stdio"]
    }
  }
}
```

### Available MCP Tools

- `get_resume` — Get the full resume as structured data
- `get_resume_section` — Get a specific section (contact, summary, experience, education, skills)
- `update_section` — Update contact info or summary text
- `add_entry` — Add a new entry to experience, education, or skills
- `update_entry` — Update an existing entry by index
- `remove_entry` — Remove an entry by index

## Data storage

Resume data is stored in a SQLite database at `~/.persona/persona.db` (or `./data/persona.db` in Docker). The database and schema are created automatically on first run — no setup required.

### Schema migrations

The database schema is versioned using SQLite's `PRAGMA user_version`. When you upgrade to a new version, migrations are applied automatically on startup. Each migration runs in a transaction — if it fails, the database is left unchanged.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PERSONA_PORT` | `8000` | HTTP server port |
| `PERSONA_DATA_DIR` | `~/.persona` | Database directory |
| `PERSONA_CORS_ORIGINS` | (empty) | Comma-separated allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |

## Development

### Root Commands (orchestrates both frontend and backend)

```bash
make check      # lint + typecheck + test (both)
make build      # build frontend then backend
make run        # docker compose up --build
make run-local  # build frontend, run backend locally
make test       # test both
make lint       # lint both
make format     # auto-format both
```

### Backend Development (from `backend/`)

```bash
cd backend
make check      # lint + typecheck + test
make test       # uv run pytest
make lint       # ruff check + format check
make run        # uv run persona (HTTP server on :8000)
make format     # auto-format with ruff
```

### Frontend Development (from `frontend/`)

```bash
cd frontend
make check      # lint + test
make build      # npm run build (production build)
make run        # npm run dev (dev server with HMR on :5173)
make lint       # npm run lint (ESLint)
make test       # npm run test (Vitest)
```

### Development Workflow

For frontend development with live backend:
1. Start backend: `cd backend && make run` (port 8000)
2. Start frontend: `cd frontend && make run` (port 5173, proxies API calls to 8000)
3. Access dev UI at `http://localhost:5173/`

For production-like testing:
1. Build frontend: `cd frontend && make build`
2. Start backend: `cd backend && make run`
3. Access UI at `http://localhost:8000/` (backend serves frontend assets)

## Docker Commands

```bash
make docker-build  # Build Docker image
make docker-up     # Start containers in background
make docker-down   # Stop containers

# View logs
docker compose logs -f

# Data persistence
# Resume data is stored in ./data/ directory (mounted as volume)
```

## Architecture

- **Frontend**: React 18 SPA built with Vite + TypeScript, uses CSS Modules for styling
- **Backend**: FastAPI + FastMCP for dual REST/MCP interface
- **Database**: SQLite with automatic schema migrations
- **Business Logic**: Shared `ResumeService` class used by REST API, MCP, and web UI
- **Unified Serving**: FastAPI serves frontend static assets at `/` with API routes at `/api/*`
- **Transport Modes**:
  - HTTP server (default): Web UI + REST API + MCP over streamable-http
  - stdio mode (`--stdio` flag): MCP over stdio for local clients

### Project Structure

```
frontend/          # React SPA (TypeScript, Vite, Vitest)
  src/
    components/    # React components (view + edit modes)
    services/      # API client (fetch wrapper)
    types/         # TypeScript definitions
backend/           # Python FastAPI + MCP server
  src/persona/     # Python package
    server.py      # FastAPI + static serving + MCP
    api/routes.py  # REST API
    tools/         # MCP tools
  tests/           # pytest (unit, contract, integration)
Dockerfile         # Multi-stage build (Node.js + Python)
Makefile           # Root orchestrator
```

## Recommended Workflow

This project uses [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with [spec-kit](https://github.com/github/spec-kit) for Spec-Driven Development (SDD) and **git worktrees** for parallel feature development.

### Setting up a new feature

```bash
# From the main working tree, create a worktree with a new feature branch
git worktree add ../worktrees/feat-005-my-feature -b feat-005-my-feature

# Open the worktree in VS Code and start Claude Code from there
code ../worktrees/feat-005-my-feature
```

### Spec-driven development (inside the worktree)

1. `/speckit.specify [feature requirements]` — generates a spec directory and initial spec. Review, edit, and re-run to refine.
2. `/speckit.clarify` — identifies gaps in the spec and asks clarifying questions.
3. `/speckit.plan [tech details]` — generates an implementation plan. Review and iterate as needed.
4. `/speckit.tasks` — produces a task list from the plan. Review and iterate as needed.
5. `/speckit.analyze` — checks alignment across spec, plan, and tasks to ensure full coverage.
6. `/speckit.implement [scope]` — executes tasks (e.g., `phase 1` or `tasks 1-4`).
7. Commit changes — in chunks or all at once, depending on feature size.
8. Push the branch.
9. Enable the GitHub MCP server (see below) and have Claude create a PR.
10. Review CI, then merge to main.

### Cleaning up after merge

```bash
# Remove the worktree after merging
git worktree remove ../worktrees/feat-005-my-feature
```

### GitHub MCP server setup (for PR creation)

```bash
# Export your GitHub PAT
export GITHUB_PAT=<your-github-pat>

# Add the GitHub MCP server
claude mcp add-json github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer '"$GITHUB_PAT"'"}}'

# Ask Claude to create a PR, then remove the server to save tokens
claude mcp remove github
```
