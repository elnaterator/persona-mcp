# Quickstart: REST API & Remote MCP Server

## Prerequisites

- Python 3.11+
- `uv` package manager
- Docker & Docker Compose (for containerized mode)

## Local Development (no Docker)

```bash
# Install dependencies
uv sync

# Run the HTTP server (REST API + MCP on streamable-http)
make run-local
# or directly:
uv run persona

# Run in stdio mode (backward compat for local MCP clients)
uv run persona --stdio
```

## Docker Development

```bash
# Build and start via Docker Compose
make run

# Or directly:
docker compose up --build
```

The server starts on `http://localhost:8000` by default:
- REST API: `http://localhost:8000/api/resume`
- MCP (streamable-http): `http://localhost:8000/mcp`
- Health check: `http://localhost:8000/health`

## Environment Variables

| Variable              | Default      | Description                           |
|-----------------------|-------------|---------------------------------------|
| `PERSONA_PORT`        | `8000`       | HTTP server port                      |
| `PERSONA_DATA_DIR`    | `~/.persona` | Database directory                    |
| `PERSONA_CORS_ORIGINS`| (empty)      | Comma-separated allowed CORS origins  |
| `LOG_LEVEL`           | `INFO`       | Logging level                         |

## Quick Test

```bash
# Get full resume
curl http://localhost:8000/api/resume

# Get a specific section
curl http://localhost:8000/api/resume/experience

# Add a skill
curl -X POST http://localhost:8000/api/resume/skills/entries \
  -H "Content-Type: application/json" \
  -d '{"name": "Python", "category": "Languages"}'

# Health check
curl http://localhost:8000/health
```

## Docker Compose

The `docker-compose.yml` at repo root defines the `persona` service:
- Builds from the local `Dockerfile`
- Maps port 8000 (configurable via `PERSONA_PORT`)
- Mounts `./data` volume for persistent database storage
- Passes environment variables through

```bash
# Start in background
docker compose up -d --build

# View logs
docker compose logs -f

# Stop
docker compose down
```

## MCP Client Configuration

### Remote (streamable-http) — new default
```json
{
  "mcpServers": {
    "persona": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Local (stdio) — backward compat
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

## Development Commands

```bash
make check      # lint + typecheck + test
make test       # run tests
make lint       # ruff check + format check
make format     # auto-format
make run        # start server via Docker Compose
make run-local  # start server without Docker
```
