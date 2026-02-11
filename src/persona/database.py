"""SQLite database operations for persona resume data."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from persona.config import DB_FILENAME
from persona.migrations import apply_migrations
from persona.models import (
    ContactInfo,
    Education,
    Resume,
    Skill,
    WorkExperience,
)

logger = logging.getLogger("persona")


def init_database(data_dir: Path) -> sqlite3.Connection:
    """Initialize the SQLite database, creating it if needed.

    Creates the data directory if it doesn't exist, opens a connection with
    WAL mode, foreign keys ON, and busy timeout, then runs any pending
    schema migrations.

    Returns the open connection ready for use.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / DB_FILENAME

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")

    apply_migrations(conn)

    logger.info("Database initialized at %s", db_path)
    return conn


# --- Read operations ---


def load_resume(conn: sqlite3.Connection) -> Resume:
    """Load the complete resume from all tables."""
    return Resume(
        contact=_load_contact(conn),
        summary=_load_summary(conn),
        experience=_load_experience(conn),
        education=_load_education(conn),
        skills=_load_skills(conn),
    )


def load_section(
    conn: sqlite3.Connection, section: str
) -> ContactInfo | str | list[WorkExperience] | list[Education] | list[Skill]:
    """Load a single resume section by name."""
    loaders = {
        "contact": _load_contact,
        "summary": _load_summary,
        "experience": _load_experience,
        "education": _load_education,
        "skills": _load_skills,
    }
    if section not in loaders:
        raise ValueError(
            f"Invalid section: '{section}'. Must be one of: {', '.join(loaders)}"
        )
    return loaders[section](conn)


def _load_contact(conn: sqlite3.Connection) -> ContactInfo:
    row = conn.execute("SELECT * FROM contact WHERE id = 1").fetchone()
    if row is None:
        return ContactInfo()
    return ContactInfo(
        name=row["name"],
        email=row["email"],
        phone=row["phone"],
        location=row["location"],
        linkedin=row["linkedin"],
        website=row["website"],
        github=row["github"],
    )


def _load_summary(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT text FROM summary WHERE id = 1").fetchone()
    if row is None:
        return ""
    return row["text"]


def _load_experience(conn: sqlite3.Connection) -> list[WorkExperience]:
    rows = conn.execute("SELECT * FROM experience ORDER BY position").fetchall()
    return [
        WorkExperience(
            title=row["title"],
            company=row["company"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            location=row["location"],
            highlights=json.loads(row["highlights"]),
        )
        for row in rows
    ]


def _load_education(conn: sqlite3.Connection) -> list[Education]:
    rows = conn.execute("SELECT * FROM education ORDER BY position").fetchall()
    return [
        Education(
            institution=row["institution"],
            degree=row["degree"],
            field=row["field"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            honors=row["honors"],
        )
        for row in rows
    ]


def _load_skills(conn: sqlite3.Connection) -> list[Skill]:
    rows = conn.execute("SELECT * FROM skill ORDER BY id").fetchall()
    return [Skill(name=row["name"], category=row["category"]) for row in rows]


# --- Write operations: singletons ---


def save_contact(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    """Save contact info with partial merge semantics."""
    known_fields = set(ContactInfo.model_fields.keys())
    filtered = {k: v for k, v in data.items() if k in known_fields}
    if not filtered:
        raise ValueError("At least one contact field must be provided")

    existing = _load_contact(conn)
    updated = existing.model_copy(update=filtered)

    conn.execute(
        "INSERT OR REPLACE INTO contact "
        "(id, name, email, phone, location, linkedin, website, github) "
        "VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
        (
            updated.name,
            updated.email,
            updated.phone,
            updated.location,
            updated.linkedin,
            updated.website,
            updated.github,
        ),
    )
    conn.commit()


def save_summary(conn: sqlite3.Connection, text: str) -> None:
    """Save summary text (full replace)."""
    if not text:
        raise ValueError("Summary text must not be empty")
    conn.execute("INSERT OR REPLACE INTO summary (id, text) VALUES (1, ?)", (text,))
    conn.commit()


# --- Write operations: list entries ---


def add_experience(conn: sqlite3.Connection, data: dict[str, Any]) -> WorkExperience:
    """Add a new experience entry at position 0 (prepend)."""
    entry = WorkExperience(**data)
    conn.execute("UPDATE experience SET position = position + 1")
    conn.execute(
        "INSERT INTO experience "
        "(title, company, start_date, end_date, location, highlights, position) "
        "VALUES (?, ?, ?, ?, ?, ?, 0)",
        (
            entry.title,
            entry.company,
            entry.start_date,
            entry.end_date,
            entry.location,
            json.dumps(entry.highlights),
        ),
    )
    conn.commit()
    return entry


def update_experience(
    conn: sqlite3.Connection, index: int, data: dict[str, Any]
) -> WorkExperience:
    """Update an experience entry at the given index (0-based by position)."""
    row = conn.execute(
        "SELECT * FROM experience WHERE position = ?", (index,)
    ).fetchone()
    if row is None:
        count = conn.execute("SELECT COUNT(*) FROM experience").fetchone()[0]
        raise ValueError(
            f"Experience index {index} out of range. "
            f"Resume has {count} experience entries."
        )

    existing = WorkExperience(
        title=row["title"],
        company=row["company"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        location=row["location"],
        highlights=json.loads(row["highlights"]),
    )
    updated = existing.model_copy(update=data)

    conn.execute(
        "UPDATE experience SET title=?, company=?, start_date=?, end_date=?, "
        "location=?, highlights=? WHERE id=?",
        (
            updated.title,
            updated.company,
            updated.start_date,
            updated.end_date,
            updated.location,
            json.dumps(updated.highlights),
            row["id"],
        ),
    )
    conn.commit()
    return updated


def remove_experience(conn: sqlite3.Connection, index: int) -> WorkExperience:
    """Remove an experience entry by index and compact positions."""
    row = conn.execute(
        "SELECT * FROM experience WHERE position = ?", (index,)
    ).fetchone()
    if row is None:
        count = conn.execute("SELECT COUNT(*) FROM experience").fetchone()[0]
        raise ValueError(
            f"Experience index {index} out of range. "
            f"Resume has {count} experience entries."
        )

    removed = WorkExperience(
        title=row["title"],
        company=row["company"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        location=row["location"],
        highlights=json.loads(row["highlights"]),
    )

    conn.execute("DELETE FROM experience WHERE id = ?", (row["id"],))
    conn.execute(
        "UPDATE experience SET position = position - 1 WHERE position > ?",
        (index,),
    )
    conn.commit()
    return removed


def add_education(conn: sqlite3.Connection, data: dict[str, Any]) -> Education:
    """Add a new education entry at position 0 (prepend)."""
    entry = Education(**data)
    conn.execute("UPDATE education SET position = position + 1")
    conn.execute(
        "INSERT INTO education "
        "(institution, degree, field, start_date, end_date, honors, position) "
        "VALUES (?, ?, ?, ?, ?, ?, 0)",
        (
            entry.institution,
            entry.degree,
            entry.field,
            entry.start_date,
            entry.end_date,
            entry.honors,
        ),
    )
    conn.commit()
    return entry


def update_education(
    conn: sqlite3.Connection, index: int, data: dict[str, Any]
) -> Education:
    """Update an education entry at the given index (0-based by position)."""
    row = conn.execute(
        "SELECT * FROM education WHERE position = ?", (index,)
    ).fetchone()
    if row is None:
        count = conn.execute("SELECT COUNT(*) FROM education").fetchone()[0]
        raise ValueError(
            f"Education index {index} out of range. "
            f"Resume has {count} education entries."
        )

    existing = Education(
        institution=row["institution"],
        degree=row["degree"],
        field=row["field"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        honors=row["honors"],
    )
    updated = existing.model_copy(update=data)

    conn.execute(
        "UPDATE education SET institution=?, degree=?, field=?, start_date=?, "
        "end_date=?, honors=? WHERE id=?",
        (
            updated.institution,
            updated.degree,
            updated.field,
            updated.start_date,
            updated.end_date,
            updated.honors,
            row["id"],
        ),
    )
    conn.commit()
    return updated


def remove_education(conn: sqlite3.Connection, index: int) -> Education:
    """Remove an education entry by index and compact positions."""
    row = conn.execute(
        "SELECT * FROM education WHERE position = ?", (index,)
    ).fetchone()
    if row is None:
        count = conn.execute("SELECT COUNT(*) FROM education").fetchone()[0]
        raise ValueError(
            f"Education index {index} out of range. "
            f"Resume has {count} education entries."
        )

    removed = Education(
        institution=row["institution"],
        degree=row["degree"],
        field=row["field"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        honors=row["honors"],
    )

    conn.execute("DELETE FROM education WHERE id = ?", (row["id"],))
    conn.execute(
        "UPDATE education SET position = position - 1 WHERE position > ?",
        (index,),
    )
    conn.commit()
    return removed


def add_skill(conn: sqlite3.Connection, data: dict[str, Any]) -> Skill:
    """Add a new skill entry. Rejects case-insensitive duplicates."""
    entry = Skill(**data)

    existing = conn.execute(
        "SELECT name, category FROM skill WHERE LOWER(name) = LOWER(?)",
        (entry.name,),
    ).fetchone()
    if existing:
        raise ValueError(
            f"Skill '{entry.name}' already exists "
            f"under category '{existing['category']}'"
        )

    conn.execute(
        "INSERT INTO skill (name, category) VALUES (?, ?)",
        (entry.name, entry.category),
    )
    conn.commit()
    return entry


def update_skill(conn: sqlite3.Connection, index: int, data: dict[str, Any]) -> Skill:
    """Update a skill entry at the given index (0-based by id ordering)."""
    rows = conn.execute("SELECT * FROM skill ORDER BY id").fetchall()
    if index < 0 or index >= len(rows):
        raise ValueError(
            f"Skills index {index} out of range. Resume has {len(rows)} skills entries."
        )

    row = rows[index]
    existing = Skill(name=row["name"], category=row["category"])
    updated = existing.model_copy(update=data)

    conn.execute(
        "UPDATE skill SET name=?, category=? WHERE id=?",
        (updated.name, updated.category, row["id"]),
    )
    conn.commit()
    return updated


def remove_skill(conn: sqlite3.Connection, index: int) -> Skill:
    """Remove a skill entry by index (0-based by id ordering)."""
    rows = conn.execute("SELECT * FROM skill ORDER BY id").fetchall()
    if index < 0 or index >= len(rows):
        raise ValueError(
            f"Skills index {index} out of range. Resume has {len(rows)} skills entries."
        )

    row = rows[index]
    removed = Skill(name=row["name"], category=row["category"])

    conn.execute("DELETE FROM skill WHERE id = ?", (row["id"],))
    conn.commit()
    return removed
