"""Shared test fixtures for persona MCP server tests."""

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from backend.migrations import MIGRATIONS, apply_migrations

# --- SQLite fixtures ---


@pytest.fixture
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    """Create an in-memory SQLite database at the current schema version."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    apply_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture
def db_conn_at_version(
    request: pytest.FixtureRequest,
) -> Generator[sqlite3.Connection, None, None]:
    """Create a DB at a specific schema version.

    Usage: @pytest.mark.parametrize(
        "db_conn_at_version", [0, 1], indirect=True
    )
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    version = request.param
    for i in range(version):
        MIGRATIONS[i](conn)
        conn.execute(f"PRAGMA user_version = {i + 1}")
        conn.commit()
    yield conn
    conn.close()


# --- Legacy markdown fixtures (kept for backward compatibility during migration) ---


SAMPLE_RESUME_MD = """\
---
name: "Jane Doe"
email: "jane@example.com"
phone: "+1-555-0100"
location: "San Francisco, CA"
linkedin: "https://linkedin.com/in/janedoe"
website: "https://janedoe.dev"
github: "https://github.com/janedoe"
---

## Summary

Experienced software engineer with 10 years of experience.

## Experience

### Senior Software Engineer | Acme Corp
- **Start**: 2021-01
- **End**: present
- **Location**: San Francisco, CA

- Led migration of monolithic application to microservices
- Reduced deployment time by 60%

### Software Engineer | StartupCo
- **Start**: 2018-06
- **End**: 2020-12
- **Location**: New York, NY

- Built real-time data pipeline processing 1M events/day
- Mentored 3 junior engineers

## Education

### M.S. Computer Science | Stanford University
- **Start**: 2016-09
- **End**: 2018-05
- **Honors**: Dean's List

### B.S. Computer Science | UC Berkeley
- **Start**: 2012-09
- **End**: 2016-05

## Skills

### Programming Languages
- Python
- TypeScript
- Go

### Frameworks
- FastAPI
- React
- Kubernetes

### Soft Skills
- Technical Leadership
- Mentoring
"""

EMPTY_RESUME_MD = """\
---
---
"""


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory with jobs/resume/ structure."""
    resume_dir = tmp_path / "jobs" / "resume"
    resume_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_resume_path(tmp_data_dir: Path) -> Path:
    """Create a sample resume.md in the tmp data directory."""
    resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
    resume_path.write_text(SAMPLE_RESUME_MD)
    return resume_path


@pytest.fixture
def empty_resume_path(tmp_data_dir: Path) -> Path:
    """Create an empty resume.md in the tmp data directory."""
    resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
    resume_path.write_text(EMPTY_RESUME_MD)
    return resume_path


def populate_sample_data(conn: sqlite3.Connection) -> None:
    """Insert sample resume data into a database for testing.

    Mirrors the SAMPLE_RESUME_MD content for contract/integration tests.
    """
    conn.execute(
        "INSERT INTO contact "
        "(id, name, email, phone, location, linkedin, website, github) "
        "VALUES (1, 'Jane Doe', 'jane@example.com', '+1-555-0100', "
        "'San Francisco, CA', 'https://linkedin.com/in/janedoe', "
        "'https://janedoe.dev', 'https://github.com/janedoe')"
    )
    conn.execute(
        "INSERT INTO summary (id, text) "
        "VALUES (1, 'Experienced software engineer with 10 years of experience.')"
    )

    # Experience (position 0 = first/newest)
    conn.execute(
        "INSERT INTO experience "
        "(title, company, start_date, end_date, location, highlights, position) "
        "VALUES ('Senior Software Engineer', 'Acme Corp', '2021-01', 'present', "
        "'San Francisco, CA', "
        '\'["Led migration of monolithic application to microservices", '
        '"Reduced deployment time by 60%"]\', 0)'
    )
    conn.execute(
        "INSERT INTO experience "
        "(title, company, start_date, end_date, location, highlights, position) "
        "VALUES ('Software Engineer', 'StartupCo', '2018-06', '2020-12', "
        "'New York, NY', "
        '\'["Built real-time data pipeline processing 1M events/day", '
        '"Mentored 3 junior engineers"]\', 1)'
    )

    # Education (position 0 = first)
    conn.execute(
        "INSERT INTO education "
        "(institution, degree, field, start_date, end_date, honors, position) "
        "VALUES ('Stanford University', 'M.S. Computer Science', NULL, "
        "'2016-09', '2018-05', 'Dean''s List', 0)"
    )
    conn.execute(
        "INSERT INTO education "
        "(institution, degree, field, start_date, end_date, honors, position) "
        "VALUES ('UC Berkeley', 'B.S. Computer Science', NULL, '2012-09', "
        "'2016-05', NULL, 1)"
    )

    # Skills
    skills = [
        ("Python", "Programming Languages"),
        ("TypeScript", "Programming Languages"),
        ("Go", "Programming Languages"),
        ("FastAPI", "Frameworks"),
        ("React", "Frameworks"),
        ("Kubernetes", "Frameworks"),
        ("Technical Leadership", "Soft Skills"),
        ("Mentoring", "Soft Skills"),
    ]
    for name, category in skills:
        conn.execute(
            "INSERT INTO skill (name, category) VALUES (?, ?)", (name, category)
        )

    conn.commit()


@pytest.fixture
def db_conn_with_data(db_conn: sqlite3.Connection) -> sqlite3.Connection:
    """Database connection pre-populated with sample resume data."""
    populate_sample_data(db_conn)
    return db_conn


# --- ResumeService fixtures ---


@pytest.fixture
def resume_service(db_conn: sqlite3.Connection):  # type: ignore[no-untyped-def]
    """ResumeService backed by an empty in-memory database."""
    from backend.resume_service import ResumeService

    return ResumeService(db_conn)


@pytest.fixture
def resume_service_with_data(db_conn_with_data: sqlite3.Connection):  # type: ignore[no-untyped-def]
    """ResumeService backed by a database pre-populated with sample data."""
    from backend.resume_service import ResumeService

    return ResumeService(db_conn_with_data)
