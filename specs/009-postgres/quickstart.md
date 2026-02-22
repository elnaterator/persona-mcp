# Quickstart: PostgreSQL Migration (009-postgres)

**Date**: 2026-02-20

---

## Running Locally

### Prerequisites

- Docker and Docker Compose installed and running
- Clerk environment variables set (same as before): `CLERK_JWKS_URL`, `CLERK_ISSUER`, `CLERK_WEBHOOK_SECRET`

### Start everything

```bash
make run
```

This starts:
1. A `postgres:16-alpine` container with data persisted in a named Docker volume (`pg-data`)
2. The `persona` app container (waits for Postgres health check before starting)
3. Schema migrations run automatically at app startup

First cold start takes ~10–15 seconds for Postgres to initialize. Subsequent starts are faster.

### Verify it's working

```bash
curl http://localhost:8000/health
# → 200 OK

curl -X GET http://localhost:8000/api/resume-versions
# → [] (empty on fresh install)
```

### Inspect the database

```bash
docker compose exec postgres psql -U persona -d persona
```

```sql
-- Check schema version
SELECT version FROM schema_version;

-- List tables
\dt
```

### Environment variables

For local development outside Docker, create a `.env` file or export:

```bash
export PERSONA_DB_URL=postgresql://persona:persona@localhost:5432/persona
export CLERK_JWKS_URL=...
export CLERK_ISSUER=...
export CLERK_WEBHOOK_SECRET=...
```

The docker-compose.yml sets `PERSONA_DB_URL` automatically for the container.

---

## Running Tests

### Prerequisites

- Docker running (required for testcontainers to spin up a PostgreSQL container)
- Python 3.11+ and `uv` installed

### Run all tests

```bash
make test        # from repo root
# or
cd backend && make test
```

On first run, testcontainers will pull `postgres:16-alpine` (~85MB) if not already cached. Subsequent runs use the cached image.

### Run a specific test file

```bash
cd backend
uv run pytest tests/unit/test_database.py -v
```

### Run the full check (lint + typecheck + test)

```bash
make check
```

---

## Test Architecture

### How test isolation works

Each test that touches the database gets a **fresh transaction** that is rolled back after the test completes. The PostgreSQL container and schema are created **once per test session**:

```
Session start: start PostgresContainer → apply migrations (once)
                     ↓
Test 1: BEGIN → [test runs] → ROLLBACK  (no data left)
Test 2: BEGIN → [test runs] → ROLLBACK  (no data left)
...
Session end:  stop container
```

This means:
- Tests are fully isolated — no cross-test contamination
- The schema is only created once (fast)
- Each test starts with a clean database state

### Test layers

| Layer | Fixture | When to use |
|-------|---------|-------------|
| **Unit (no DB)** | `MagicMock()` or stub satisfying `DBConnection` | Business logic that doesn't need real SQL semantics |
| **DB integration** | `db_conn` (PostgreSQL + transaction rollback) | Testing SQL queries, constraints, migrations |
| **Contract / API** | `test_client` backed by `db_conn` | Testing REST endpoints end-to-end |

### Writing a new DB-dependent test

```python
# Example: testing a new database operation
def test_my_new_operation(db_conn):
    """db_conn is a real PostgreSQL connection, auto-rolled back after test."""
    from persona.database import my_new_operation

    result = my_new_operation(db_conn, {"field": "value"})

    assert result["id"] is not None
    assert result["field"] == "value"
```

### Writing a pure unit test (no DB)

```python
from unittest.mock import MagicMock

def test_business_logic_no_db():
    """Pure unit test — no container, no network, instant."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = {"id": 1, "label": "test"}

    from persona.resume_service import ResumeService
    service = ResumeService(mock_conn)
    # ... assert on service behavior
```

---

## Connecting to PostgreSQL (Development)

### Start just Postgres for local backend development

```bash
docker compose up postgres -d
```

Then run the backend locally:

```bash
PERSONA_DB_URL=postgresql://persona:persona@localhost:5432/persona \
CLERK_JWKS_URL=... \
CLERK_ISSUER=... \
CLERK_WEBHOOK_SECRET=... \
make run-local
```

### Data persistence

Data is stored in the `pg-data` Docker volume. To **reset all data**:

```bash
docker compose down -v   # removes volumes
make run                 # fresh start
```

To **keep data** across restarts:

```bash
docker compose down      # no -v flag
make run                 # data survives
```
