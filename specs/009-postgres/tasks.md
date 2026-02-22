# Tasks: PostgreSQL Migration & Test Strategy (009-postgres)

**Input**: Design documents from `specs/009-postgres/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**User Stories**:
- **US1 (P1)**: `make run` works with PostgreSQL via docker-compose (no SQLite)
- **US2 (P2)**: Full test suite passes against real PostgreSQL (testcontainers)
- **US3 (P3)**: Documented test patterns for writing new DB-dependent tests

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in all descriptions

---

## Phase 1: Setup (Dependencies & Configuration)

**Purpose**: Add new runtime and dev dependencies; no source changes yet

- [X] T001 Add `"psycopg[binary]>=3.1"` and `"psycopg-pool>=3.1"` as two separate entries to `[project.dependencies]`, and `"testcontainers[postgres]>=4.0"` and `"pytest-randomly>=3.0"` to `[dependency-groups].dev` in `backend/pyproject.toml`, then run `uv lock` from `backend/`

---

## Phase 2: Foundational (Blocking Prerequisites — TDD-ordered)

**Purpose**: Core backend infrastructure. Each module that changes production behaviour follows strict TDD: write failing tests first, then implement. Must be complete before US1 or US2 phase work can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### 2a — Config & Protocol (minor additions, no TDD cycle needed)

- [X] T002 [P] Add `resolve_db_url()`, `resolve_pool_min()` (default 1), and `resolve_pool_max()` (default 10) to `backend/src/persona/config.py`; keep existing resolvers untouched
- [X] T003 [P] Update docstring on `DBConnection` protocol in `backend/src/persona/db.py` to document that `psycopg.Connection` satisfies the protocol; remove any SQLite-specific documentation (no signature changes)

### 2b — Migrations (TDD: red → green)

- [X] T004a Rewrite `backend/tests/unit/test_migrations.py` **first** (red phase): replace `sqlite3.connect(":memory:")` with a self-contained **module-scoped** inline testcontainers fixture (`PostgresContainer` + direct `psycopg.connect` — no conftest.py dependency); replace all `PRAGMA user_version` assertions with `SELECT version FROM schema_version` queries; add a test that `schema_version` is bootstrapped on first run; add a test that a failing migration rolls back atomically. **`db_conn_at_version` no longer exists — replace its usage with direct calls to individual migration functions on a bare connection, then assert the resulting schema state (option b: verify per-migration final state, not intermediate states via parametrized fixture).** Run `uv run pytest tests/unit/test_migrations.py` — tests **MUST FAIL** before proceeding to T004b.
- [X] T004b Implement `backend/src/persona/migrations.py` (green phase): replace `PRAGMA user_version` with `schema_version` table bootstrap; replace `executescript()` with individual `conn.execute()` calls; port all DDL to PostgreSQL dialect (`SERIAL`, `CURRENT_TIMESTAMP`, `TIMESTAMP`, `%s`, remove `PRAGMA foreign_keys`); preserve `MigrationError` and `SchemaVersionError` classes; each migration function must execute DDL + `UPDATE schema_version SET version = %s` and `conn.commit()` in one atomic block. Run `uv run pytest tests/unit/test_migrations.py` — tests **MUST PASS** before proceeding.

### 2c — Test Fixture Infrastructure (unlocked by T004b)

- [X] T008 Rewrite `backend/tests/conftest.py`: replace SQLite in-memory fixtures with testcontainers-backed PostgreSQL fixtures. Add session-scoped `pg_container` (PostgresContainer "postgres:16-alpine", driver=None), `pg_dsn` (extracts DSN), and `_schema_applied` (calls `apply_migrations` once, now available from T004b) fixtures. Rewrite function-scoped `db_conn` to `BEGIN` + yield + `ROLLBACK` against `pg_dsn`. Preserve existing fixture names (`db_conn`, `db_conn_with_data`, `resume_service`, `resume_service_with_data`). **Remove `db_conn_at_version`** — migration tests (T004a) use self-contained inline fixtures and no longer need it. Add a module docstring explaining the three-layer hierarchy: `pg_container` (session, starts once), `_schema_applied` (session, migrations once), `db_conn` (function, BEGIN/ROLLBACK per test).

### 2d — Database Operations (TDD: red → green)

- [X] T005a Rewrite `backend/tests/unit/test_database.py` **first** (red phase): replace any SQLite-specific fixture or pragma references with PostgreSQL equivalents using `db_conn` from the updated conftest.py (T008); remove SQLite-specific PRAGMA tests (WAL mode, foreign_keys, busy_timeout); add assertions for `RETURNING id` behaviour and `ILIKE` search semantics. Run `uv run pytest tests/unit/test_database.py` — tests **MUST FAIL** before proceeding to T005b.
- [X] T005b Rewrite `backend/src/persona/database.py` (green phase): change all `?` placeholders to `%s`; change `LOWER(col) LIKE ?` to `col ILIKE %s`; change `datetime('now')` to `CURRENT_TIMESTAMP`; change `cursor.lastrowid` to `INSERT … RETURNING id` + `cursor.fetchone()["id"]` (note: `dict_row` returns a dict — `[0]` would raise `TypeError`); remove `conn.row_factory = sqlite3.Row` and all SQLite PRAGMAs; rename `init_database(data_dir)` to `init_pool(dsn, min_size, max_size) -> ConnectionPool` returning a `psycopg_pool.ConnectionPool` configured with `row_factory=dict_row`. Run `uv run pytest tests/unit/test_database.py` — tests **MUST PASS** before proceeding.

**Checkpoint**: Foundation complete — all unit tests for migrations and database operations are green against PostgreSQL.

---

## Phase 3: User Story 1 — `make run` with PostgreSQL (Priority: P1) 🎯 MVP

**Goal**: `make run` (i.e., `docker compose up --build`) starts a `postgres:16-alpine` container and the persona app container; the app connects to PostgreSQL, runs migrations at startup, and serves requests normally. No SQLite file or volume is used.

**Independent Test**: After `make run`, `curl http://localhost:8000/health` returns 200 OK and `docker compose exec postgres psql -U persona -d persona -c "SELECT version FROM schema_version;"` returns the current schema version integer.

- [X] T006 [P] [US1] Update `docker-compose.yml`: add `postgres` service (`postgres:16-alpine`, env POSTGRES_USER/PASSWORD/DB=persona, `pg_isready` healthcheck, `pg-data` named volume); add `PERSONA_DB_URL=postgresql://persona:persona@postgres:5432/persona` env var to `persona` service; add `depends_on: postgres: condition: service_healthy`; remove `persona-data` volume and `PERSONA_DATA_DIR` env var
- [X] T007 [P] [US1] Update `backend/src/persona/server.py`: replace `init_database(data_dir)` with `init_pool(dsn, min_size, max_size)` using config resolvers; open pool in `lifespan` startup and close in shutdown; replace global `_conn` with `_pool`; update `get_db()` FastAPI dependency to yield `pool.connection()` context manager; update MCP stdio `main()` path to call `init_pool(resolve_db_url(), ...)` and hold a single connection checkout for the process lifetime

**Checkpoint**: `make run` works end-to-end with PostgreSQL. `curl http://localhost:8000/health` → 200 OK. All existing REST endpoints function against PostgreSQL data.

---

## Phase 4: User Story 2 — Test Suite Passes Against PostgreSQL (Priority: P2)

**Goal**: `make check` (lint + typecheck + test) passes in full. All remaining test files (integration, contract) are wired to the PostgreSQL-backed fixtures. Per-test transaction rollback keeps tests isolated.

**Independent Test**: `cd backend && uv run pytest -v` completes with 0 failures; no `sqlite3` imports remain in test files.

**Note**: `test_migrations.py` and `test_database.py` were already updated in Phase 2 (TDD red→green). This phase wires the remaining integration and contract test files.

- [X] T011 [P] [US2] Update `backend/tests/integration/test_server.py`: replace `init_database` / `sqlite3` / `tmp_path` DB setup with pool-backed `TestClient` using `db_conn`; replace `PRAGMA user_version` assertions with `SELECT version FROM schema_version`; update any `sqlite3.connect` calls used for direct DB inspection
- [X] T012 [P] [US2] Update `backend/tests/contract/test_mcp_resume.py` (and any sibling contract test files): ensure `TestClient` or MCP test harness uses the PostgreSQL-backed `db_conn` fixture; remove any SQLite-specific setup
- [X] T013 [P] [US2] Update `backend/tests/contract/test_rest_resume.py`, `test_rest_applications.py`, `test_rest_accomplishments.py`: same PostgreSQL fixture wiring as T012 — confirm each file compiles and imports resolve after `database.py` rename of `init_database`
- [X] T014 [US2] Run `cd backend && uv run pytest -v` and fix any remaining test failures due to SQL dialect differences (e.g., `lastrowid` references, `sqlite3.OperationalError` catches that should become `psycopg.OperationalError`); run `uv run ruff check src/ tests/` and fix any linting issues; verify isolation holds under random ordering with `uv run pytest -v -p randomly --randomly-seed=12345`

**Checkpoint**: `make check` passes (lint + typecheck + tests). 0 test failures. No `sqlite3` references in source or tests (except possibly a comment).

---

## Phase 5: User Story 3 — Documented Test Patterns (Priority: P3)

**Goal**: A developer writing a new DB-dependent test can follow clear, in-code patterns without consulting external docs. The `conftest.py` and README provide sufficient guidance.

**Independent Test**: A developer can write a new `test_foo(db_conn)` test following examples in conftest.py and it runs correctly with automatic rollback.

- [X] T015 [P] [US3] Add inline usage examples to the module docstring in `backend/tests/conftest.py` (T008 added the hierarchy docstring; this task adds "how to use" examples): show `test_foo(db_conn)` pattern, `test_pure_logic()` with MagicMock, and `test_api(test_client, db_conn)` pattern
- [X] T016 [P] [US3] Add a "Writing Tests" section to `backend/README.md` (or create it if it doesn't exist) linking to `specs/009-postgres/quickstart.md` and showing the three test patterns: pure unit test (MagicMock), DB integration test (db_conn), contract/API test (TestClient + db_conn)
- [X] T016b [P] [US3] Update root `README.md`: document the three new env vars (`PERSONA_DB_URL`, `PERSONA_DB_POOL_MIN`, `PERSONA_DB_POOL_MAX`) with their defaults; note that `make run` now starts a Postgres container automatically; note that `make run-local` requires `docker compose up postgres -d` first; remove any reference to `PERSONA_DATA_DIR` as a database configuration variable
- [X] T017 [US3] Verify `specs/009-postgres/quickstart.md` is accurate against the final implementation (fixture names, DSN format, `make test` commands); update any details that changed during implementation

**Checkpoint**: All three user stories complete and independently verifiable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Remove dead code, verify CI compatibility, ensure clean repo state

- [X] T018 [P] Remove dead SQLite code: delete any remaining `PERSONA_DATA_DIR` references from `backend/src/persona/config.py` if no longer used by any non-DB path; remove SQLite-specific imports (`import sqlite3`) from all source files under `backend/src/`
- [X] T019 Run full `make check` from repo root (lint + typecheck + test, both frontend and backend) and fix any remaining issues; confirm output shows 0 failures; verify `make run` cold-start completes in under 30 seconds per SC-001

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundation)**: Depends on Phase 1; internal ordering is strict (see below)
- **Phase 3 (US1)**: Depends on Phase 2 — T006 (docker-compose) needs no Python deps but T007 (server.py) needs T002, T004b, T005b
- **Phase 4 (US2)**: Depends on Phase 2 (conftest.py T008 must be done; T011–T013 use `db_conn`)
- **Phase 5 (US3)**: Depends on Phase 4 (docs must reflect final implementation)
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5 complete

### Within Phase 2 (Foundation — strict TDD ordering)

```
T001 (pyproject.toml + uv lock)
  → T002 [P] (config.py)       — parallel, no test cycle needed
  → T003 [P] (db.py)           — parallel, no test cycle needed
  → T004a (write failing migration tests)   ← MUST FAIL
  → T004b (implement migrations.py)         ← MUST PASS
  → T008  (rewrite conftest.py)             ← needs apply_migrations from T004b
  → T005a (write failing database tests)    ← MUST FAIL
  → T005b (implement database.py)           ← MUST PASS
```

### Within Phase 3 (US1)

```
T002, T004b, T005b complete
  → T006 [P] (docker-compose.yml)  — different file from T007
  → T007 [P] (server.py)           — different file from T006
Both touch different files → run in parallel
```

### Within Phase 4 (US2)

```
T008 complete (from Phase 2)
  → T011 [P]  (test_server.py)
  → T012 [P]  (test_mcp_resume.py)
  → T013 [P]  (contract tests)
All T011–T013 can run in parallel (different files)
  → T014 (run pytest + fix failures + random-order verification)
```

---

## Parallel Execution Examples

### Phase 2: TDD red→green cycles (sequential within module, parallel across unrelated files)

```bash
# Round 1: migrations (sequential — red must precede green)
Task: "Write failing migration tests in backend/tests/unit/test_migrations.py"  # T004a → MUST FAIL
Task: "Implement backend/src/persona/migrations.py for PostgreSQL"               # T004b → MUST PASS

# Then: wire conftest.py (unlocks Round 2)
Task: "Rewrite backend/tests/conftest.py with testcontainers fixtures"           # T008

# Round 2: database ops (sequential — red must precede green)
Task: "Write failing database tests in backend/tests/unit/test_database.py"      # T005a → MUST FAIL
Task: "Rewrite backend/src/persona/database.py for PostgreSQL"                   # T005b → MUST PASS

# T002 and T003 can run in parallel with any of the above (different files)
```

### Phase 3 + 4: US1 and US2 can overlap (all different files)

```bash
# Once Phase 2 completes, start all in parallel:
Task: "Update docker-compose.yml for postgres service"      # T006 (US1)
Task: "Update server.py pool lifecycle"                     # T007 (US1)
Task: "Update test_server.py for PostgreSQL"                # T011 (US2)
Task: "Update test_mcp_resume.py fixture wiring"            # T012 (US2)
Task: "Update contract test files"                          # T013 (US2)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundation (T002, T003, T004a→T004b, T008, T005a→T005b) — **CRITICAL, blocks everything**
3. Complete Phase 3: US1 (T006, T007)
4. **STOP and VALIDATE**: `make run` → `curl http://localhost:8000/health` → 200 OK
5. Deploy if ready; Phase 4 test suite update can follow

### Incremental Delivery

1. Phase 1 + 2 → Backend ported to PostgreSQL, unit tests green
2. Phase 3 (US1) → `make run` works end-to-end with Postgres
3. Phase 4 (US2) → `make check` passes fully (all test layers)
4. Phase 5 (US3) → Developer docs complete
5. Phase 6 (Polish) → Clean repo, CI green

### Single-Developer Sequential Order

```
T001 → T002, T003 (parallel) → T004a → T004b → T008 → T005a → T005b →
T006, T007 (parallel) → T011, T012, T013 (parallel) → T014 →
T015, T016, T016b (parallel) → T017 → T018, T019
```

---

## Notes

- **TDD gates**: T004a and T005a carry explicit MUST FAIL checkpoints. Do not skip the failure verification — a test that never fails cannot prove the implementation is correct.
- **T004a is self-contained**: Migration tests use their own inline testcontainers fixture (not conftest.py) so they can be written before conftest.py is rewritten. This is the key that makes the TDD cycle possible.
- **No SQLite data migration**: Fresh PostgreSQL schema on first `make run` — existing SQLite data is not carried over (by design, per spec)
- **`PERSONA_DATA_DIR`**: May still be read by non-DB code paths (e.g., static file serving); only remove in T018 if confirmed unused after database.py rewrite
- **`make run-local`**: After this feature, requires `docker compose up postgres -d` first OR `PERSONA_DB_URL` pointing to an external PostgreSQL instance
- **CI**: `ubuntu-latest` GitHub Actions runner has Docker pre-installed; testcontainers works out of the box — no workflow changes needed
- **`psycopg[binary]`**: Bundles native libpq; Dockerfile needs no system package changes
- **[P] tasks** = different files, no incomplete dependencies
- **[Story] label** maps each task to its user story for traceability
- Commit after each phase checkpoint to preserve incremental progress
