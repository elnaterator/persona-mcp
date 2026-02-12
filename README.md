# Persona MCP Server

An MCP (Model Context Protocol) server that exposes personal data — starting with resume management — to AI assistants. Now with REST API and remote MCP access over HTTP.

## Features

- **Resume Management**: Store and query your resume data (contact, summary, experience, education, skills)
- **REST API**: Full CRUD operations via HTTP at `/api/resume` endpoints  
- **Remote MCP Server**: Access MCP tools over HTTP (streamable-http transport) at `/mcp`
- **Dual Interface**: Both REST API and MCP server share the same database and business logic
- **Docker Support**: Run via Docker Compose with persistent data storage
- **SQLite Storage**: Persistent, schema-versioned database with automatic migrations
- **Type-Safe**: Full Pydantic validation and type hints throughout

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
- REST API: `http://localhost:8000/api/resume`
- MCP endpoint: `http://localhost:8000/mcp`
- Health check: `http://localhost:8000/health`

### Option 2: Local Development

```bash
# Install dependencies
uv sync

# Run the HTTP server (REST API + MCP)
make run-local
# or directly:
uv run persona

# Run in stdio mode (backward compatibility)
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

```bash
make check      # lint + typecheck + test
make test       # run tests
make lint       # ruff check + format check
make format     # auto-format
make run        # start server via Docker Compose
make run-local  # start server without Docker
```

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

- **Backend**: FastAPI + FastMCP for dual REST/MCP interface
- **Database**: SQLite with automatic schema migrations
- **Business Logic**: Shared `ResumeService` class used by both interfaces
- **Transport Modes**: 
  - HTTP server (default): REST API + MCP over streamable-http
  - stdio mode (`--stdio` flag): MCP over stdio for local clients

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
