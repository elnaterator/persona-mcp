# Implementation Plan: PostgreSQL Migration & Test Strategy

**Branch**: `009-postgres` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/009-postgres/spec.md`

## Summary

Replace the SQLite database with PostgreSQL across the full stack: update the Docker Compose setup to add a Postgres service, port schema migrations and all database operations to PostgreSQL SQL dialect (psycopg3), introduce a `ConnectionPool` for production-quality connection management, and replace the SQLite-based test fixtures with a testcontainers-based approach that provides real PostgreSQL behavior with per-test transaction rollback isolation.

## Technical Context

**Language/Version**: Python 3.11+ (backend); TypeScript 5.x / React 18 (frontend)
**Primary Dependencies**: FastAPI ≥0.100.0, FastMCP ≥2.3.0, psycopg[binary] ≥3.1, psycopg-pool ≥3.1, testcontainers[postgres] ≥4.0 (dev)
**Storage**: PostgreSQL 16+
**Testing**: pytest, testcontainers[postgres] ≥4.0
**Target Platform**: Docker container (Linux); local macOS development
**Project Type**: web
**Performance Goals**: <30s cold start on `make run`; connection pool min=1 / max=10 (configurable)
**Constraints**: No SQLite data migration; Docker required for `make run` and integration tests; `make check` must pass in CI without local PG install
**Scale/Scope**: Single-user personal tool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I — MCP Protocol Compliance | ✅ Pass | No changes to MCP tools, schemas, or lifecycle |
| II — Single-Package Distribution via uvx | ✅ Pass | New runtime deps declared in `pyproject.toml`; `psycopg[binary]` bundles its native lib (no `libpq-dev` required in Docker image) |
| III — Test-Driven Development | ✅ Pass | All new DB code must be written test-first; testcontainers fixture enables real PostgreSQL tests in TDD cycle |
| IV — Minimal Dependencies | ✅ Pass (justified) | 3 new deps: `psycopg[binary]` replaces stdlib sqlite3 (engine change mandates it); `psycopg-pool` has no stdlib equivalent; `testcontainers[postgres]` is dev-only with no alternative for CI-compatible PostgreSQL testing. All MIT/LGPL licensed. |
| V — Explicit Error Handling | ✅ Pass | Pool startup failure and migration errors must be caught and surfaced clearly; no change to MCP error handling |

**Post-design re-check**: All constraints satisfied. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/009-postgres/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── README.md        # No API contract changes; env var delta documented
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/persona/
│   ├── config.py          # Add: resolve_db_url(), resolve_pool_min/max()
│   ├── database.py        # Rewrite: SQLite ops → psycopg3 ops; ? → %s; RETURNING; ILIKE
│   ├── migrations.py      # Rewrite: schema_version table; PostgreSQL SQL dialect; DDL transactions
│   ├── db.py              # Minor: update protocol doc comment (no signature changes)
│   └── server.py          # Update: pool lifecycle (open/close in lifespan); connection checkout
├── tests/
│   ├── conftest.py        # Rewrite: testcontainers fixture; session-scoped PG; per-test rollback
│   ├── unit/
│   │   ├── test_database.py     # Update: pg fixture; remove SQLite-specific PRAGMA tests
│   │   └── test_migrations.py   # Rewrite: PostgreSQL migration tests
│   ├── contract/          # Update: wire pg-backed test client
│   └── integration/       # Update: wire pg-backed test client
├── pyproject.toml         # Add: psycopg[binary], psycopg-pool, testcontainers[postgres]

docker-compose.yml         # Update: add postgres service, depends_on, PERSONA_DB_URL
Dockerfile                 # Minor: no system libpq needed (psycopg[binary] self-contained)
```

**Structure Decision**: Web application (Option 2 from template). Backend and frontend are separate directories. No new directories are added; all changes are to existing files.

## Complexity Tracking

No Constitution violations requiring justification.

---

## Phase 0: Research Findings

**Output**: [research.md](research.md) — all decisions resolved, no NEEDS CLARIFICATION remaining.

### Key decisions

1. **Driver**: `psycopg[binary]` ≥3.1 — self-contained binary, satisfies `DBConnection` protocol
2. **Pool**: `psycopg_pool.ConnectionPool` (sync), min=1, max=10, FastAPI lifespan managed
3. **Row factory**: `psycopg.rows.dict_row` — equivalent to `sqlite3.Row` dict access
4. **Schema version**: `schema_version` table replaces `PRAGMA user_version`
5. **Test infra**: `testcontainers[postgres]` ≥4.0 (4.13.3 current), session-scoped container, function-scoped `BEGIN`/`ROLLBACK` isolation
6. **SQL dialect**: See full migration map in [research.md](research.md#decision-6-sql-dialect-migration-map)
7. **Docker Compose**: Postgres service with `pg_isready` healthcheck; `depends_on: service_healthy`
8. **MCP stdio mode**: Pool checkout held for process lifetime, returned on shutdown

---

## Phase 1: Design

### Architecture: Connection Pool Lifecycle

```
App startup (lifespan)
  → ConnectionPool(dsn, min_size=1, max_size=10) opened
  → apply_migrations(pool.getconn()) called
  → pool.wait() verifies min connections ready

HTTP request
  → get_db() dependency: pool.connection() context manager
  → connection checked out; yielded to route handler
  → on normal exit: committed; connection returned to pool
  → on exception: rolled back; connection returned to pool

MCP stdio mode
  → single connection checked out at startup
  → held for process lifetime
  → returned to pool on shutdown

App shutdown (lifespan)
  → pool.close() — drains active connections
```

### Architecture: Migration Runner (PostgreSQL)

```
apply_migrations(conn: Connection) -> None
  1. Ensure schema_version table exists (CREATE TABLE IF NOT EXISTS)
  2. Read current version (SELECT version FROM schema_version LIMIT 1)
  3. For each pending migration function:
     a. Call migration_fn(conn)  [DDL executes inside implicit transaction]
     b. UPDATE schema_version SET version = target_version
     c. conn.commit()            [DDL + version update atomic]
     d. On error: conn.rollback() + raise MigrationError
```

PostgreSQL's transactional DDL means both the schema changes AND the version number update roll back together on failure — the database is never left in a partially migrated state.

### Architecture: Test Fixture Hierarchy

```
scope=session  pg_container     — starts PostgresContainer once
scope=session  pg_dsn           — extracts DSN from container
scope=session  _schema_applied  — runs apply_migrations once
scope=function db_conn          — BEGIN; yield psycopg conn; ROLLBACK
scope=function db_conn_at_version — for migration-specific tests (new approach needed)
```

### Key File Changes

#### `backend/pyproject.toml`

Add to `[project.dependencies]`:
```toml
"psycopg[binary]>=3.1",
"psycopg-pool>=3.1",
```

Add to `[dependency-groups].dev`:
```toml
"testcontainers[postgres]>=4.0",
```

#### `backend/src/persona/config.py`

Add three new resolver functions:
```python
def resolve_db_url() -> str:
    """Resolve PERSONA_DB_URL env var. Raises ValueError if missing in HTTP mode."""

def resolve_pool_min() -> int:
    """Resolve PERSONA_DB_POOL_MIN (default: 1)."""

def resolve_pool_max() -> int:
    """Resolve PERSONA_DB_POOL_MAX (default: 10)."""
```

Remove: `DB_FILENAME`, `resolve_data_dir()` (no longer needed for DB; keep if used elsewhere for file storage).

#### `backend/src/persona/migrations.py`

- Remove all `sqlite3`-specific imports and `PRAGMA user_version` logic
- Add `schema_version` table bootstrap (runs before version check)
- Port all migration DDL: `AUTOINCREMENT` → `SERIAL`, `datetime('now')` → `CURRENT_TIMESTAMP`, `TEXT` timestamps → `TIMESTAMP`
- Replace `conn.executescript()` with multiple `conn.execute()` calls (psycopg3 does not have `executescript`)
- Each migration function receives `psycopg.Connection` (satisfies `DBConnection`)

#### `backend/src/persona/database.py`

- Change all `?` parameter placeholders to `%s`
- Change `LIKE ?` / `LOWER(col) LIKE ?` to `col ILIKE %s`
- Change `datetime('now')` in UPDATE statements to `CURRENT_TIMESTAMP`
- Change `cursor.lastrowid` lookups to `INSERT … RETURNING id` + `cursor.fetchone()[0]` (or full `RETURNING *` for single-query returns)
- Remove SQLite-specific `conn.row_factory = sqlite3.Row` (set on pool/connection at creation time)
- Remove WAL mode / foreign_keys PRAGMA / busy_timeout PRAGMA (PostgreSQL handles these natively)
- Update `init_database()` → `init_pool(dsn, min_size, max_size) -> ConnectionPool`

#### `backend/src/persona/server.py`

- Replace `init_database(data_dir)` with `init_pool(dsn, min_size, max_size)`
- Pool opened/closed in `lifespan` context manager
- Global `_conn` replaced by `_pool`; MCP tool handlers checkout a connection per call
- FastAPI dependency `get_db()` yields a connection from the pool

#### `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: persona
      POSTGRES_PASSWORD: persona
      POSTGRES_DB: persona
    volumes:
      - pg-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "persona"]
      interval: 5s
      timeout: 3s
      retries: 5

  persona:
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - PERSONA_DB_URL=postgresql://persona:persona@postgres:5432/persona
      # Remove: PERSONA_DATA_DIR (no longer needed for DB)
      # ... rest unchanged

volumes:
  pg-data:           # new
  # persona-data:    # removed (SQLite volume)
```

#### `backend/tests/conftest.py`

Replace SQLite in-memory fixtures with testcontainers-backed PostgreSQL fixtures. Maintain existing fixture names (`db_conn`, `db_conn_with_data`, `resume_service`, etc.) so that **no test files need their fixture references changed** — only the underlying implementation changes.

```python
# New: testcontainers + psycopg3 session fixtures
@pytest.fixture(scope="session")
def pg_container() -> Generator[PostgresContainer, None, None]: ...

@pytest.fixture(scope="session")
def pg_dsn(pg_container) -> str: ...

@pytest.fixture(scope="session")
def _schema_applied(pg_dsn) -> None: ...

# Updated: function-scoped (same name, PostgreSQL backed)
@pytest.fixture
def db_conn(_schema_applied, pg_dsn) -> Generator[Connection, None, None]:
    """BEGIN + yield + ROLLBACK — per-test isolation."""
```

The `db_conn_at_version` fixture for migration tests needs a fresh schema per call (cannot use the session-level migrated schema). It will create a new connection on a freshly-bootstrapped database (or use savepoints).

---

## Open Questions / Implementation Notes

1. **`db_conn_at_version` fixture**: The existing fixture lets tests verify the schema at intermediate versions (e.g., v1, v2). With PostgreSQL, this is trickier — we can't reuse the session schema. Options: (a) use separate connections with `SAVEPOINT`/`ROLLBACK TO SAVEPOINT` and re-run migrations from scratch within a savepoint, or (b) rewrite migration tests to verify the final schema state only and test individual migration functions in isolation. **Recommendation**: option (b) — simpler and more maintainable.

2. **`make run-local`**: The root Makefile `run-local` target builds the frontend then runs the backend locally. It currently does not start Postgres. After this feature, `run-local` should document that Postgres must be started separately (e.g., `docker compose up postgres -d`) or the target should be updated to start Postgres as a side effect.

3. **`--stdio` mode**: The `main()` function's `--stdio` path currently calls `init_database(data_dir)`. After this feature, it calls `init_pool(dsn, ...)` and holds a checkout for the process lifetime. `PERSONA_DB_URL` must be set in the environment for stdio mode to work.

4. **Dockerfile**: `psycopg[binary]` includes the libpq binary statically. No system packages (`libpq-dev`) need to be added to the Dockerfile. The existing `python:3.11-slim` base is sufficient.
