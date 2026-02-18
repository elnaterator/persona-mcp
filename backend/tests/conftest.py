"""Shared test fixtures for persona MCP server tests."""

import json
import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from persona.migrations import MIGRATIONS, apply_migrations

# --- SQLite fixtures ---


@pytest.fixture
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    """Create an in-memory SQLite database at the current schema version."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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


# --- Sample resume data as dict (for v2 JSON blob) ---

SAMPLE_RESUME_DATA = {
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


def populate_sample_data(conn: sqlite3.Connection) -> None:
    """Populate the default resume version with sample data.

    The migration creates an empty default version. This updates it
    with sample data for testing.
    """
    conn.execute(
        "UPDATE resume_version SET resume_data = ? WHERE is_default = 1",
        (json.dumps(SAMPLE_RESUME_DATA),),
    )
    conn.commit()


# --- Legacy markdown fixtures (kept for backward compatibility) ---


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


@pytest.fixture
def db_conn_with_data(db_conn: sqlite3.Connection) -> sqlite3.Connection:
    """Database connection pre-populated with sample resume data."""
    populate_sample_data(db_conn)
    return db_conn


# --- ResumeService fixtures ---


@pytest.fixture
def resume_service(db_conn: sqlite3.Connection):  # type: ignore[no-untyped-def]
    """ResumeService backed by an empty in-memory database."""
    from persona.resume_service import ResumeService

    return ResumeService(db_conn)


@pytest.fixture
def resume_service_with_data(db_conn_with_data: sqlite3.Connection):  # type: ignore[no-untyped-def]
    """ResumeService backed by a database pre-populated with sample data."""
    from persona.resume_service import ResumeService

    return ResumeService(db_conn_with_data)
