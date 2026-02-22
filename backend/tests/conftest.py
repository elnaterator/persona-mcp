"""Shared test fixtures for persona MCP server tests.

Three-layer fixture hierarchy
------------------------------
1. ``pg_container`` (session-scoped): starts one ``postgres:16-alpine``
   container for the entire test session.
2. ``_schema_applied`` (session-scoped): applies all migrations exactly once
   against a dedicated session-level schema so the DDL cost is paid once.
3. ``db_conn`` (function-scoped): opens a fresh psycopg connection, issues
   ``BEGIN``, yields, then ``ROLLBACK`` — every test sees a clean slate with
   no data leakage between tests.

Usage examples
--------------
Pure unit test (no DB needed)::

    def test_pure_logic() -> None:
        from unittest.mock import MagicMock
        conn = MagicMock()
        # test business logic in isolation

DB integration test::

    def test_foo(db_conn) -> None:
        from persona.database import create_application
        app = create_application(db_conn, {"company": "Acme", "position": "Dev"})
        assert app["company"] == "Acme"
        # db_conn automatically rolls back after this test

API / contract test::

    def test_api(test_client, db_conn) -> None:
        response = test_client.post("/api/applications", json={...})
        assert response.status_code == 201
"""

import json
from collections.abc import Generator
from typing import Any

import psycopg
import pytest
from psycopg import Connection
from psycopg.rows import dict_row
from testcontainers.postgres import PostgresContainer

# ---------------------------------------------------------------------------
# Layer 1: session-scoped container (starts once per test session)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def pg_container():
    """Start a postgres:16-alpine container once for the entire test session."""
    with PostgresContainer("postgres:16-alpine", driver=None) as container:
        yield container


# ---------------------------------------------------------------------------
# Layer 2: session-scoped DSN + migrations applied once
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def pg_dsn(pg_container) -> str:
    """Extract the plain DSN from the running container."""
    return pg_container.get_connection_url()


@pytest.fixture(scope="session")
def _schema_applied(pg_dsn: str) -> None:
    """Apply all migrations exactly once per test session."""
    from persona.migrations import apply_migrations

    with psycopg.connect(pg_dsn) as conn:
        apply_migrations(conn)


# ---------------------------------------------------------------------------
# Layer 3: function-scoped connection with BEGIN / ROLLBACK per test
# ---------------------------------------------------------------------------


@pytest.fixture
def db_conn(_schema_applied, pg_dsn: str) -> Generator[Connection[Any], None, None]:
    """Per-test PostgreSQL connection with automatic rollback.

    Each test runs inside a transaction that is rolled back on teardown,
    ensuring no data leaks between tests. Database functions must NOT call
    conn.commit() — transaction lifecycle is managed here and by the pool
    context manager in production.
    """
    with psycopg.connect(pg_dsn, row_factory=dict_row, autocommit=False) as conn:  # type: ignore[call-overload]
        yield conn
        conn.rollback()


# ---------------------------------------------------------------------------
# Sample resume data
# ---------------------------------------------------------------------------


SAMPLE_RESUME_DATA: dict[str, Any] = {
    "contact": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
        "location": "San Francisco, CA",
        "linkedin": "https://linkedin.com/in/janedoe",
        "website": "https://janedoe.dev",
        "github": "https://github.com/janedoe",
    },
    "summary": "Experienced software engineer with 10 years of experience.",
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Acme Corp",
            "start_date": "2021-01",
            "end_date": "present",
            "location": "San Francisco, CA",
            "highlights": [
                "Led migration of monolithic application to microservices",
                "Reduced deployment time by 60%",
            ],
        },
        {
            "title": "Software Engineer",
            "company": "StartupCo",
            "start_date": "2018-06",
            "end_date": "2020-12",
            "location": "New York, NY",
            "highlights": [
                "Built real-time data pipeline processing 1M events/day",
                "Mentored 3 junior engineers",
            ],
        },
    ],
    "education": [
        {
            "institution": "Stanford University",
            "degree": "M.S. Computer Science",
            "field": None,
            "start_date": "2016-09",
            "end_date": "2018-05",
            "honors": "Dean's List",
        },
        {
            "institution": "UC Berkeley",
            "degree": "B.S. Computer Science",
            "field": None,
            "start_date": "2012-09",
            "end_date": "2016-05",
            "honors": None,
        },
    ],
    "skills": [
        {"name": "Python", "category": "Programming Languages"},
        {"name": "TypeScript", "category": "Programming Languages"},
        {"name": "Go", "category": "Programming Languages"},
        {"name": "FastAPI", "category": "Frameworks"},
        {"name": "React", "category": "Frameworks"},
        {"name": "Kubernetes", "category": "Frameworks"},
        {"name": "Technical Leadership", "category": "Soft Skills"},
        {"name": "Mentoring", "category": "Soft Skills"},
    ],
}


def populate_sample_data(conn: Connection[Any]) -> None:
    """Populate the default resume version with sample data.

    The migration creates an empty default version. This updates it
    with sample data for testing.
    """
    conn.execute(
        "UPDATE resume_version SET resume_data = %s WHERE is_default = 1",
        (json.dumps(SAMPLE_RESUME_DATA),),
    )


@pytest.fixture
def db_conn_with_data(db_conn: Connection[Any]) -> Connection[Any]:
    """Database connection pre-populated with sample resume data."""
    populate_sample_data(db_conn)
    return db_conn


# ---------------------------------------------------------------------------
# ResumeService fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def resume_service(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    """ResumeService backed by a PostgreSQL database."""
    from persona.resume_service import ResumeService

    return ResumeService(db_conn)  # type: ignore[arg-type]


@pytest.fixture
def resume_service_with_data(db_conn_with_data: Connection[Any]):  # type: ignore[no-untyped-def]
    """ResumeService backed by a database pre-populated with sample data."""
    from persona.resume_service import ResumeService

    return ResumeService(db_conn_with_data)  # type: ignore[arg-type]
