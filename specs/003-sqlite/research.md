# Research: SQLite Storage Migration

**Feature**: feat-003-sqlite
**Date**: 2026-02-11

## 1. SQLite Storage Approach

**Decision**: Use Python stdlib `sqlite3` module directly — no ORM.

**Rationale**:
- The constitution (Principle IV: Minimal Dependencies) mandates preferring the standard library when it provides equivalent functionality. `sqlite3` is built into Python 3.11+.
- The project already has Pydantic models for validation. Adding SQLAlchemy would duplicate the modeling layer and introduce a large transitive dependency footprint.
- For a single-user tool with 5 entities and simple CRUD, raw SQL is clear and maintainable.
- The future Postgres aspiration is noted but out of scope. When that time comes, a lightweight adapter or SQLAlchemy introduction can be evaluated independently. The migration framework (version tracking + sequential migrations) will transfer regardless.

**Alternatives considered**:
- **SQLAlchemy Core** (no ORM, just SQL expression language): Rejected — adds ~15MB dependency for marginal benefit on a 5-table schema. Constitution requires justification for every dependency.
- **SQLAlchemy ORM**: Rejected — duplicates Pydantic validation layer, heavyweight for this use case.
- **Peewee**: Rejected — lighter than SQLAlchemy but still an unnecessary dependency for this scope.

## 2. Schema Migration Pattern

**Decision**: Use SQLite's built-in `PRAGMA user_version` for version tracking, with sequential Python functions as migrations.

**Rationale**:
- `PRAGMA user_version` is a free integer stored in the SQLite file header — no extra table needed for version tracking.
- Each migration is a Python function (not a SQL file) named `migrate_vN_to_vN1()`, registered in an ordered list. This allows data transformations that require Python logic, not just DDL.
- Each migration runs inside a transaction. On failure, the transaction rolls back and the version stays unchanged.
- On startup: read `user_version`, compare to `len(migrations)`, apply any pending migrations sequentially.
- Forward-only: no downgrade functions (per spec assumption).

**Pattern**:
```python
# migrations are functions: (connection) -> None
# migration 0→1 is migrations[0], 1→2 is migrations[1], etc.
MIGRATIONS = [
    migrate_v0_to_v1,  # initial schema
    migrate_v1_to_v2,  # example future migration
]
SCHEMA_VERSION = len(MIGRATIONS)

def apply_migrations(conn):
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current > SCHEMA_VERSION:
        raise SchemaVersionError(current, SCHEMA_VERSION)
    for i in range(current, SCHEMA_VERSION):
        with conn:  # transaction context
            MIGRATIONS[i](conn)
            conn.execute(f"PRAGMA user_version = {i + 1}")
```

**Alternatives considered**:
- **SQL file-based migrations** (numbered `.sql` files in a directory): Rejected — Python functions are more flexible for data transformations and don't require file I/O at runtime. Also avoids packaging concerns with `uvx`.
- **Separate `schema_version` table**: Rejected — `PRAGMA user_version` is simpler and purpose-built for this.
- **Alembic**: Explicitly out of scope per spec.

## 3. Connection Management

**Decision**: Single connection created at startup, stored as module-level state. WAL mode enabled. No connection pooling.

**Rationale**:
- This is a single-user MCP server on stdio transport. There is exactly one client at a time.
- WAL (Write-Ahead Logging) mode allows concurrent reads during writes — useful if the server ever handles overlapping requests, and has no downside for single-user.
- `check_same_thread=False` is needed because FastMCP may dispatch tool handlers on different threads/tasks than the connection was created on.
- Connection lifecycle: open on server start, close on server shutdown. No per-request connection creation.

**Configuration pragmas** (set once after connection):
```python
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA foreign_keys = ON")
conn.execute("PRAGMA busy_timeout = 5000")
```

**Alternatives considered**:
- **Per-request connections**: Rejected — unnecessary overhead for single-user, and complicates migration/initialization.
- **Connection pool**: Rejected — no concurrent users to serve.
- **async aiosqlite**: Rejected — adds a dependency. The MCP server's tool handlers are synchronous (FastMCP runs them in a thread pool), so stdlib `sqlite3` works directly.

## 4. Testing SQLite

**Decision**: Use in-memory SQLite databases (`:memory:`) with function-scoped pytest fixtures for test isolation.

**Rationale**:
- In-memory databases are fast (no disk I/O) and automatically cleaned up.
- Function-scoped fixtures ensure each test starts with a clean database — no state leakage between tests.
- Migration tests specifically need: (a) a fixture that creates a DB at version N, (b) applies migrations, (c) verifies schema and data.
- The existing test structure (unit/, contract/, integration/) is preserved.

**Test fixture pattern**:
```python
@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)  # brings to current schema
    yield conn
    conn.close()

@pytest.fixture
def db_conn_at_version(request):
    """Create a DB at a specific schema version for migration tests."""
    conn = sqlite3.connect(":memory:")
    version = request.param
    for i in range(version):
        MIGRATIONS[i](conn)
        conn.execute(f"PRAGMA user_version = {i + 1}")
    yield conn
    conn.close()
```

**Test categories**:
- **Unit tests**: Database module functions (CRUD operations, validation, error paths)
- **Contract tests**: MCP tool handlers produce correct output with SQLite backend (same contracts, new storage)
- **Integration tests**: End-to-end through MCP server with real SQLite
- **Migration tests**: Schema upgrades preserve data, version mismatch detection, rollback on failure

**Alternatives considered**:
- **Temp file databases**: Rejected for unit/contract tests — slower than in-memory. May be useful for integration tests that need to test file creation behavior.
- **Shared fixtures (module/session scope)**: Rejected — test isolation is more important than speed for this small test suite.

## 5. Pydantic ↔ SQLite Mapping

**Decision**: Manual mapping with helper functions. Use `model_dump()` for writes, constructor kwargs for reads. Store nested lists as JSON text columns.

**Rationale**:
- Pydantic models are the source of truth for validation. SQLite stores the data; Pydantic validates it.
- The `highlights` field on `WorkExperience` (a `list[str]`) doesn't map naturally to a relational column. Options: (a) separate table, (b) JSON column. JSON column is simpler and sufficient — highlights are always read/written as a unit, never queried individually.
- Skills use a separate table row per skill (not JSON) because they have uniqueness constraints and are individually addressable.

**Write pattern** (Pydantic → SQLite):
```python
def save_experience(conn, exp: WorkExperience, position: int):
    conn.execute(
        "INSERT INTO experience (title, company, start_date, end_date, location, highlights, position) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (exp.title, exp.company, exp.start_date, exp.end_date, exp.location, json.dumps(exp.highlights), position),
    )
```

**Read pattern** (SQLite → Pydantic):
```python
def load_experience(conn) -> list[WorkExperience]:
    rows = conn.execute("SELECT * FROM experience ORDER BY position").fetchall()
    return [
        WorkExperience(
            title=row["title"], company=row["company"],
            start_date=row["start_date"], end_date=row["end_date"],
            location=row["location"], highlights=json.loads(row["highlights"]),
        )
        for row in rows
    ]
```

**Alternatives considered**:
- **Separate `highlights` table** (one row per highlight): Rejected — over-normalized for data that's always read/written as a list. Adds JOIN complexity for no query benefit.
- **Pickle/marshal for nested data**: Rejected — not human-readable, not portable, security concerns.
- **Store entire Resume as single JSON blob**: Rejected — loses all relational benefits (individual entry CRUD, uniqueness constraints, ordering).
