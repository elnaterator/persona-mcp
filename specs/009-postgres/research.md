# Research: PostgreSQL Migration (009-postgres)

**Date**: 2026-02-20
**Phase**: 0 — Unknowns resolved

---

## Decision 1: PostgreSQL Driver

**Decision**: `psycopg[binary]` (psycopg3) ≥3.1
**Rationale**: The `[binary]` extra bundles the native C extension pre-compiled, eliminating the need for `libpq-dev` on the build host or in the Docker image. psycopg3 is the actively-maintained successor to psycopg2, has native async support for future use, and its `Connection` object satisfies the existing `DBConnection` protocol without changes.
**Alternatives considered**:
- `asyncpg`: async-only; incompatible with synchronous FastAPI handlers and the `DBConnection` protocol.
- `psycopg2-binary`: older API, officially in maintenance mode.
- `aiomysql` / other adapters: wrong engine.

---

## Decision 2: Connection Pool

**Decision**: `psycopg-pool.ConnectionPool` (separate `psycopg-pool` package), min=1, max=10
**Rationale**: `ConnectionPool` (synchronous) is correct for synchronous FastAPI route handlers running in Uvicorn's thread pool. It replaces the single shared `sqlite3.Connection` with proper multi-connection pooling, eliminating the threading workarounds (`check_same_thread=False`, `cached_statements=0`, `isolation_level=None`) currently in `database.py`. The pool lifecycle is managed in FastAPI's `lifespan` context manager.
**Connection checkout pattern**:
```python
# FastAPI dependency
def get_db() -> Generator[Connection, None, None]:
    with pool.connection() as conn:   # checks out; auto-commit on success, rollback on exception
        yield conn
```
**Alternatives considered**:
- Single shared connection (current): requires threading hacks; not idiomatic for PostgreSQL.
- One connection per request (no pool): wastes TCP handshake latency; no connection reuse.
- `AsyncConnectionPool`: requires async handlers throughout; not compatible with current sync handlers.

---

## Decision 3: Row Factory

**Decision**: `psycopg.rows.dict_row`
**Rationale**: Equivalent to `sqlite3.Row` dict access. Each row returned as a plain `dict`, matching the existing `dict(row)` and `row["column"]` patterns throughout `database.py` with no code changes beyond the factory configuration.
**Alternatives considered**: `namedtuple_row` — attribute access only; would require changing all column access patterns.

---

## Decision 4: Schema Version Tracking

**Decision**: Dedicated `schema_version` table with a single integer row
**Rationale**: PostgreSQL has no equivalent of `PRAGMA user_version`. A single-row table is the idiomatic minimal approach. It participates in PostgreSQL's transactional DDL — the version number update and schema DDL execute in the same transaction, guaranteeing they never diverge even on crash.
```sql
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
INSERT INTO schema_version (version) VALUES (0) ON CONFLICT DO NOTHING;
```
**Version read**: `SELECT version FROM schema_version LIMIT 1`
**Version write**: `UPDATE schema_version SET version = %s`
**Alternatives considered**: `pg_catalog` / advisory locks: more complex with no benefit for a single-instance tool.

---

## Decision 5: Test Infrastructure

**Decision**: `testcontainers[postgres]` ≥4.0 (latest: 4.13.3 as of Jan 2026), session-scoped container, function-scoped transaction rollback
**Rationale**: Works on any machine with Docker (including GitHub Actions CI) without a local `pg_ctl` binary. A single container starts once per test session (schema applied once); each test runs inside an explicit `BEGIN`/`ROLLBACK` so no data leaks between tests. This is substantially faster than recreating the schema per test.

**Fixture pattern** (canonical, to be implemented in `conftest.py`):
```python
from testcontainers.postgres import PostgresContainer
import psycopg
from psycopg.rows import dict_row

@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16-alpine", driver=None) as container:
        yield container

@pytest.fixture(scope="session")
def pg_dsn(pg_container) -> str:
    return pg_container.get_connection_url()  # returns plain DSN (driver=None)

@pytest.fixture(scope="session")
def _schema_applied(pg_dsn):
    """Apply migrations once per session."""
    from persona.migrations import apply_migrations
    with psycopg.connect(pg_dsn) as conn:
        apply_migrations(conn)

@pytest.fixture
def db_conn(_schema_applied, pg_dsn):
    """Per-test PostgreSQL connection with automatic rollback."""
    with psycopg.connect(pg_dsn, row_factory=dict_row) as conn:
        conn.execute("BEGIN")
        yield conn
        conn.rollback()
```
**Alternatives considered**:
- `pytest-postgresql`: requires local `pg_ctl`; fails on CI runners without PostgreSQL install. NOT used.
- Schema recreation per test: correct but 10-50× slower at scale.
- SQLite in-memory (current): cannot validate PostgreSQL-specific behavior.

---

## Decision 6: SQL Dialect Migration Map

All changes required when porting migrations and database operations from SQLite to PostgreSQL:

| Construct | SQLite (current) | PostgreSQL |
|-----------|-----------------|------------|
| Auto-increment PK | `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| Timestamp default | `DEFAULT (datetime('now'))` | `DEFAULT CURRENT_TIMESTAMP` |
| Timestamp column type | `TEXT` | `TIMESTAMP` |
| Parameter placeholder | `?` | `%s` |
| Case-insensitive search | `LOWER(col) LIKE ?` | `col ILIKE %s` |
| Upsert | `ON CONFLICT(id) DO UPDATE SET` | identical |
| Partial index | `WHERE is_default = 1` | identical |
| Insert + get ID | `cursor.lastrowid` | `INSERT … RETURNING id` |
| Schema version | `PRAGMA user_version` | `schema_version` table |
| JSON text default | `TEXT DEFAULT '[]'` | identical (keep TEXT for now) |
| DDL transactions | Implicit auto-commit (limited) | Full support — DDL rolls back on error |
| `datetime('now')` in UPDATE | `SET updated_at = datetime('now')` | `SET updated_at = CURRENT_TIMESTAMP` |

---

## Decision 7: Docker Compose Architecture

**Decision**: Add `postgres` service alongside `persona` service; `persona` depends on postgres with health check.
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
      PERSONA_DB_URL: postgresql://persona:persona@postgres:5432/persona
```
**Rationale**: Health check ensures the app never starts before PostgreSQL is ready to accept connections. Named volume `pg-data` persists data across restarts.
**Alternatives considered**: Startup retry loop in app code alone (without depends_on health check): works but allows Docker Compose to report services as started before they're ready.

---

## Decision 8: pyproject.toml Dependency Changes

**New runtime dependencies** (added to `[project.dependencies]`):
- `psycopg[binary]>=3.1` — PostgreSQL adapter with bundled binary
- `psycopg-pool>=3.1` — synchronous connection pool

**New dev/test dependencies** (added to `[dependency-groups].dev`):
- `testcontainers[postgres]>=4.0` — Docker-based PostgreSQL test infrastructure

**Removed**: Nothing is removed from `pyproject.toml`; `sqlite3` is stdlib and was never listed.

**Constitution IV compliance**: All three new packages are justified — `psycopg[binary]` replaces stdlib sqlite3 (the engine change mandates it); `psycopg-pool` enables production-quality connection management with no stdlib equivalent; `testcontainers` is dev-only and is the only option that works in CI without a local PostgreSQL install. All licenses are MIT/LGPL-compatible.

---

## Decision 9: MCP stdio Mode

**Decision**: In `--stdio` mode, the app opens a single connection directly from the pool (min=1 ensures one is always available) rather than using the FastAPI dependency injection system.
**Rationale**: stdio mode bypasses FastAPI's request lifecycle. The existing pattern of holding a single `_conn` for MCP tool handlers can be replaced with a pool checkout that is held for the lifetime of the stdio process and returned on shutdown.

---

## Unresolved / Deferred

None. All NEEDS CLARIFICATION items resolved.
