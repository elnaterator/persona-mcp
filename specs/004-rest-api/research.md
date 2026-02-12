# Research: REST API & Remote MCP Server with Docker Support

**Date**: 2026-02-12
**Feature**: feat-004-rest-api

## R-001: FastMCP Streamable-HTTP Integration with FastAPI

**Decision**: Use the standalone `fastmcp>=2.3.0` package instead of the built-in `mcp.server.fastmcp`.

**Rationale**: The standalone `fastmcp` package provides `http_app(path="/")` with a configurable path parameter and a `combine_lifespans` utility, both critical for clean FastAPI integration. The built-in `mcp.server.fastmcp.streamable_http_app()` has a hardcoded `/mcp` internal route that causes double-path issues when mounted on a sub-path (known issue: GitHub modelcontextprotocol/python-sdk#1367).

**Alternatives considered**:
- `mcp.server.fastmcp.streamable_http_app()` (built-in): Rejected due to hardcoded path and awkward sub-mount behavior.
- Separate MCP process: Rejected — spec requires single-process shared state.

**Integration pattern**:
```python
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.utilities.lifespan import combine_lifespans

mcp = FastMCP("persona")
mcp_app = mcp.http_app(path="/")

app = FastAPI(lifespan=combine_lifespans(app_lifespan, mcp_app.lifespan))
app.mount("/mcp", mcp_app)
```

## R-002: HTTP Server Framework

**Decision**: FastAPI with uvicorn as the ASGI server.

**Rationale**: FastAPI provides automatic OpenAPI docs, Pydantic model integration (already used in the project), and CORSMiddleware. Uvicorn is the standard production ASGI server for FastAPI. The project already uses Pydantic models, so FastAPI's native support gives request/response validation for free.

**Alternatives considered**:
- Starlette (bare): Rejected — FastAPI adds Pydantic integration and auto-docs at minimal cost.
- Flask/Quart: Rejected — not ASGI-native, harder to mount alongside FastMCP's ASGI app.

## R-003: CORS Configuration

**Decision**: Use FastAPI's `CORSMiddleware` with origins parsed from `PERSONA_CORS_ORIGINS` environment variable (comma-separated). Empty/unset = no CORS (restrictive default).

**Rationale**: Standard FastAPI pattern. Environment variable matches existing config approach (PERSONA_DATA_DIR, LOG_LEVEL). Restrictive default prevents accidental exposure.

## R-004: Generic Database Connection Type (DBConnection Protocol)

**Decision**: Define a `typing.Protocol` called `DBConnection` that captures the PEP 249 DB-API 2.0 methods we actually use. Use this as the type annotation throughout business logic. Keep SQLite-specific initialization code isolated in `database.py`.

**Rationale**: Python's DB-API 2.0 (PEP 249) defines a standard interface but the standard library provides no `Protocol` or ABC for it. Both `sqlite3.Connection` and `psycopg`/`psycopg2` connections implement the same core methods. A custom Protocol gives structural typing — any compliant connection satisfies it without inheritance.

**Protocol shape**:
```python
from typing import Protocol, Any

class DBConnection(Protocol):
    def execute(self, sql: str, parameters: Any = ...) -> Any: ...
    def cursor(self) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...
```

**SQLite-specific code** (WAL mode, `row_factory`, `executescript`, PRAGMAs) stays isolated in `database.py`'s `init_database()` function, which returns an object that satisfies `DBConnection`.

**Alternatives considered**:
- `sqlite3.Connection` type everywhere: Rejected — user explicitly wants DB-agnostic types for future PostgreSQL migration.
- `Union[sqlite3.Connection, psycopg.Connection]`: Rejected — requires importing both drivers, tight coupling.
- Third-party `pep249` package: Rejected — adds dependency for type hints only; violates Principle IV (minimal dependencies).

## R-005: ResumeService Class Pattern

**Decision**: Create a `ResumeService` class that takes a `DBConnection` in its constructor. All resume CRUD operations become instance methods. Both REST API routes and MCP tools use the same `ResumeService` instance.

**Rationale**: User explicitly requested class-based service with constructor injection to avoid passing the connection to every function call. Also provides a clean seam for testing (inject a test DB connection) and future DB swaps (inject a PostgreSQL connection).

**Class shape**:
```python
class ResumeService:
    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn

    def get_resume(self) -> Resume: ...
    def get_section(self, section: str) -> dict: ...
    def update_section(self, section: str, data: dict) -> None: ...
    def add_entry(self, section: str, data: dict) -> dict: ...
    def update_entry(self, section: str, index: int, data: dict) -> dict: ...
    def remove_entry(self, section: str, index: int) -> None: ...
```

**Alternatives considered**:
- Keep function-based approach with `functools.partial`: Rejected — user explicitly wants class-based.
- Repository pattern with separate repositories per entity: Rejected — over-engineering for 5 tables.

## R-006: Package Rename (src/persona → src/backend)

**Decision**: Rename the source directory from `src/persona/` to `src/backend/`. The Python package becomes `backend`. The CLI entry point remains `persona` (script name is independent of package name in pyproject.toml).

**Rationale**: User explicitly requested `src/backend`. This prepares for a future frontend directory alongside the backend. The `persona` command name is preserved via `pyproject.toml`'s `[project.scripts]` mapping: `persona = "backend.server:main"`.

**Impact**:
- All imports change: `from persona.X` → `from backend.X`
- pyproject.toml entry point: `persona = "backend.server:main"`
- Test imports updated accordingly
- Hatchling package discovery points to `src/backend`

**Alternatives considered**:
- Keep `src/persona/` directory name: Rejected — user explicitly wants `src/backend`.
- Nest as `src/backend/persona/`: Rejected — unnecessary nesting, confusing.

## R-007: Docker Compose Setup

**Decision**: Add `docker-compose.yml` at repo root with a single `persona` service. Add `Dockerfile` for the app image. Update Makefile: `make run` uses docker compose, `make run-local` runs without docker.

**Rationale**: User explicitly requested docker-compose (not just Dockerfile). Docker Compose provides declarative service definition with volume mounts, port mapping, and environment variables. Separating `make run` (docker) from `make run-local` (native) gives clear development modes.

**Docker strategy**:
- Multi-stage build: builder stage with `uv` for dependency install, slim runtime stage
- Base image: `python:3.11-slim`
- Volume: `./data:/data` for persistent SQLite database
- Port: configurable, default 8000
- Health check: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"` (no curl needed in slim image)

**Makefile changes**:
- `make run` → `docker compose up --build` (replaces current `uv run persona`)
- `make run-local` → `uv run persona` (preserves non-docker workflow)

**Alternatives considered**:
- Dockerfile only (no compose): Rejected — user explicitly requested compose.
- Separate docker-compose files for dev/prod: Rejected — over-engineering for now.

## R-008: stdio Backward Compatibility

**Decision**: The `persona` CLI defaults to HTTP server mode. A `--stdio` flag switches to stdio MCP transport for backward compatibility with local MCP clients (e.g., Claude Desktop).

**Rationale**: Per FR-011, the HTTP server is the new default. Existing stdio users get a migration path via the flag. stdio mode skips FastAPI/uvicorn entirely and runs the MCP server directly.

**Alternatives considered**:
- Keep stdio as default, `--http` flag for new mode: Rejected — spec explicitly states HTTP is the new default.
- Remove stdio entirely: Rejected — breaks existing local MCP client configurations.

## R-009: Dependency Changes

**Decision**: Add these dependencies to `pyproject.toml`:
- `fastmcp>=2.3.0` (replaces `mcp>=1.0.0` — fastmcp depends on mcp internally)
- `fastapi>=0.100.0`
- `uvicorn>=0.20.0`

**Rationale**: Minimal additions. `fastmcp` subsumes `mcp` as a dependency so the direct `mcp` dependency can be replaced. FastAPI and uvicorn are the standard ASGI stack.
