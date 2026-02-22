# Persona Backend

Python FastAPI + FastMCP server for the Persona MCP application.

## Development Commands

```bash
make check    # lint + typecheck + test
make test     # uv run pytest
make lint     # ruff check + format check
make format   # auto-format with ruff
make run      # uv run persona (HTTP server — requires PERSONA_DB_URL)
```

## Writing Tests

For a comprehensive guide including running locally with Docker, see
[`specs/009-postgres/quickstart.md`](../specs/009-postgres/quickstart.md).

### Test Architecture

Tests use a three-layer fixture hierarchy defined in `tests/conftest.py`:

1. **Session-scoped container** — one `postgres:16-alpine` started per test run
2. **Session-scoped migrations** — schema applied once against that container
3. **Function-scoped connection** — each test gets `BEGIN`/`ROLLBACK` isolation

### Pattern 1: Pure unit test (no DB)

Use `MagicMock` for business logic that doesn't need real SQL semantics.
No container, no network — instant.

```python
from unittest.mock import MagicMock

def test_business_logic_no_db() -> None:
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = {"id": 1, "label": "test"}

    from persona.resume_service import ResumeService
    service = ResumeService(conn)
    # ... assert on service behavior
```

### Pattern 2: DB integration test

Use the `db_conn` fixture for tests that need real SQL semantics (constraints,
`ILIKE` search, `RETURNING id`, etc.). The connection is automatically rolled back
after each test — no data leaks between tests.

```python
import psycopg

def test_create_application(db_conn: psycopg.Connection) -> None:
    from persona.database import create_application

    app = create_application(db_conn, user_id="user_1", data={"company": "Acme", "position": "Dev"})

    assert app["id"] is not None
    assert app["company"] == "Acme"
    # db_conn rolls back automatically after this test
```

### Pattern 3: Contract / API test

Use `TestClient` with a service backed by `db_conn` for end-to-end REST endpoint
testing. Combine `db_conn` (for direct DB assertions) with `TestClient` for HTTP.

```python
import psycopg
import pytest
from starlette.testclient import TestClient

from persona.api.routes import create_router
from persona.resume_service import ResumeService


@pytest.fixture
def client(db_conn: psycopg.Connection) -> TestClient:
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(create_router(ResumeService(db_conn)))
    return TestClient(app)


def test_create_resume(client: TestClient, db_conn: psycopg.Connection) -> None:
    response = client.post("/api/resumes", json={"label": "My Resume", "resume_data": {}})
    assert response.status_code == 201
    assert response.json()["label"] == "My Resume"
```

### Test file locations

| Layer | Directory | Fixture |
|-------|-----------|---------|
| Unit (no DB) | `tests/unit/` | `MagicMock` |
| Unit (with DB) | `tests/unit/` | `db_conn` |
| Contract / API | `tests/contract/` | `db_conn` + `TestClient` |
| Integration | `tests/integration/` | `db_conn` + full app |

### Running tests

```bash
# All tests (requires Docker running for testcontainers)
cd backend && make test

# Specific file
uv run pytest tests/unit/test_database.py -v

# With random ordering (verify isolation)
uv run pytest -v -p randomly --randomly-seed=12345

# Full check (lint + typecheck + test)
make check
```
