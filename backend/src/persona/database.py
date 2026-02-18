"""SQLite database operations for persona resume data."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from persona.config import DB_FILENAME
from persona.db import DBConnection
from persona.migrations import apply_migrations

logger = logging.getLogger("persona")


def init_database(data_dir: Path) -> DBConnection:
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


# --- Resume Version operations ---


def _row_to_resume_data(row: Any) -> dict[str, Any]:
    """Convert a resume_version row to a dict with parsed resume_data."""
    return {
        "id": row["id"],
        "label": row["label"],
        "is_default": bool(row["is_default"]),
        "resume_data": json.loads(row["resume_data"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_resume_version(
    conn: DBConnection, label: str, resume_data: dict[str, Any]
) -> dict[str, Any]:
    """Create a new resume version. Returns the created version."""
    data_json = json.dumps(resume_data)
    cursor = conn.execute(
        "INSERT INTO resume_version (label, is_default, resume_data) VALUES (?, 0, ?)",
        (label, data_json),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return _row_to_resume_data(row)


def load_resume_version(conn: DBConnection, version_id: int) -> dict[str, Any]:
    """Load a resume version by ID. Raises ValueError if not found."""
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = ?", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")
    return _row_to_resume_data(row)


def load_resume_versions(conn: DBConnection) -> list[dict[str, Any]]:
    """Load all resume versions with metadata and app_count."""
    rows = conn.execute(
        "SELECT rv.id, rv.label, rv.is_default, rv.created_at, rv.updated_at, "
        "COUNT(a.id) AS app_count "
        "FROM resume_version rv "
        "LEFT JOIN application a ON a.resume_version_id = rv.id "
        "GROUP BY rv.id "
        "ORDER BY rv.id"
    ).fetchall()
    return [
        {
            "id": row["id"],
            "label": row["label"],
            "is_default": bool(row["is_default"]),
            "app_count": row["app_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def load_default_resume_version(conn: DBConnection) -> dict[str, Any]:
    """Load the default resume version. Raises ValueError if none."""
    row = conn.execute("SELECT * FROM resume_version WHERE is_default = 1").fetchone()
    if row is None:
        raise ValueError("No default resume version found")
    return _row_to_resume_data(row)


def update_resume_version_metadata(
    conn: DBConnection, version_id: int, label: str
) -> dict[str, Any]:
    """Update resume version label. Returns updated version."""
    row = conn.execute(
        "SELECT id FROM resume_version WHERE id = ?", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")

    conn.execute(
        "UPDATE resume_version SET label = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (label, version_id),
    )
    conn.commit()
    return load_resume_version(conn, version_id)


def update_resume_version_data(
    conn: DBConnection, version_id: int, resume_data: dict[str, Any]
) -> None:
    """Update the resume_data JSON blob for a version."""
    row = conn.execute(
        "SELECT id FROM resume_version WHERE id = ?", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")

    conn.execute(
        "UPDATE resume_version "
        "SET resume_data = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (json.dumps(resume_data), version_id),
    )
    conn.commit()


def delete_resume_version(conn: DBConnection, version_id: int) -> str:
    """Delete a resume version. Returns label of deleted version.

    If deleting the default and other versions exist, auto-promotes
    the most recently updated version. Rejects deleting the last version.
    """
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = ?", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")

    label = row["label"]
    is_default = bool(row["is_default"])

    count = conn.execute("SELECT COUNT(*) FROM resume_version").fetchone()[0]
    if count <= 1:
        raise ValueError("Cannot delete the last remaining resume version")

    conn.execute("DELETE FROM resume_version WHERE id = ?", (version_id,))

    if is_default:
        # Promote most recently updated version
        conn.execute(
            "UPDATE resume_version SET is_default = 1 "
            "WHERE id = ("
            "  SELECT id FROM resume_version "
            "  ORDER BY updated_at DESC LIMIT 1"
            ")"
        )

    conn.commit()
    return label


def set_default_resume_version(conn: DBConnection, version_id: int) -> str:
    """Set a resume version as default. Returns its label."""
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = ?", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")

    label = row["label"]

    # Unset old default, set new default in same transaction
    conn.execute("UPDATE resume_version SET is_default = 0")
    conn.execute(
        "UPDATE resume_version SET is_default = 1 WHERE id = ?",
        (version_id,),
    )
    conn.commit()
    return label


# --- Application operations ---


def create_application(conn: DBConnection, data: dict[str, Any]) -> dict[str, Any]:
    """Create a new application. Returns the created application."""
    cursor = conn.execute(
        "INSERT INTO application "
        "(company, position, description, status, url, notes, "
        "resume_version_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data["company"],
            data["position"],
            data.get("description", ""),
            data.get("status", "Interested"),
            data.get("url"),
            data.get("notes", ""),
            data.get("resume_version_id"),
        ),
    )
    conn.commit()
    return load_application(conn, cursor.lastrowid)


def load_application(conn: DBConnection, app_id: int) -> dict[str, Any]:
    """Load a single application by ID."""
    row = conn.execute("SELECT * FROM application WHERE id = ?", (app_id,)).fetchone()
    if row is None:
        raise ValueError(f"Application {app_id} not found")
    return dict(row)


def load_applications(
    conn: DBConnection,
    status: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    """Load applications with optional status filter and search."""
    query = (
        "SELECT id, company, position, status, url, "
        "resume_version_id, created_at, updated_at "
        "FROM application"
    )
    conditions: list[str] = []
    params: list[Any] = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if q:
        conditions.append("(LOWER(company) LIKE ? OR LOWER(position) LIKE ?)")
        pattern = f"%{q.lower()}%"
        params.extend([pattern, pattern])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY updated_at DESC"

    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def update_application(
    conn: DBConnection, app_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Update application fields. Returns updated application."""
    existing = load_application(conn, app_id)

    updatable = (
        "company",
        "position",
        "description",
        "status",
        "url",
        "notes",
        "resume_version_id",
    )
    sets: list[str] = []
    params: list[Any] = []
    for field in updatable:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])

    if not sets:
        return existing

    sets.append("updated_at = datetime('now')")
    params.append(app_id)

    conn.execute(
        f"UPDATE application SET {', '.join(sets)} WHERE id = ?",
        params,
    )
    conn.commit()
    return load_application(conn, app_id)


def delete_application(conn: DBConnection, app_id: int) -> dict[str, Any]:
    """Delete an application and cascade. Returns deleted app data."""
    app = load_application(conn, app_id)
    conn.execute("DELETE FROM application WHERE id = ?", (app_id,))
    conn.commit()
    return app


# --- Application Contact operations ---


def create_contact(
    conn: DBConnection, app_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Create a contact for an application."""
    # Verify app exists
    load_application(conn, app_id)

    cursor = conn.execute(
        "INSERT INTO application_contact "
        "(app_id, name, role, email, phone, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            app_id,
            data["name"],
            data.get("role"),
            data.get("email"),
            data.get("phone"),
            data.get("notes", ""),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM application_contact WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row)


def load_contacts(conn: DBConnection, app_id: int) -> list[dict[str, Any]]:
    """Load all contacts for an application."""
    rows = conn.execute(
        "SELECT * FROM application_contact WHERE app_id = ? ORDER BY id",
        (app_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def update_contact(
    conn: DBConnection, contact_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Update a contact. Returns updated contact."""
    row = conn.execute(
        "SELECT * FROM application_contact WHERE id = ?",
        (contact_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Contact {contact_id} not found")

    updatable = ("name", "role", "email", "phone", "notes")
    sets: list[str] = []
    params: list[Any] = []
    for field in updatable:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])

    if not sets:
        return dict(row)

    params.append(contact_id)
    conn.execute(
        f"UPDATE application_contact SET {', '.join(sets)} WHERE id = ?",
        params,
    )
    conn.commit()
    return dict(
        conn.execute(
            "SELECT * FROM application_contact WHERE id = ?",
            (contact_id,),
        ).fetchone()
    )


def delete_contact(conn: DBConnection, contact_id: int) -> str:
    """Delete a contact. Returns contact name."""
    row = conn.execute(
        "SELECT * FROM application_contact WHERE id = ?",
        (contact_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Contact {contact_id} not found")

    name = row["name"]
    conn.execute("DELETE FROM application_contact WHERE id = ?", (contact_id,))
    conn.commit()
    return name


# --- Communication operations ---


def create_communication(
    conn: DBConnection, app_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Create a communication. Auto-populates contact_name from contact_id."""
    load_application(conn, app_id)

    contact_name = data.get("contact_name")
    contact_id = data.get("contact_id")
    if contact_id is not None:
        contact_row = conn.execute(
            "SELECT name FROM application_contact WHERE id = ?",
            (contact_id,),
        ).fetchone()
        if contact_row:
            contact_name = contact_row["name"]

    cursor = conn.execute(
        "INSERT INTO communication "
        "(app_id, contact_id, contact_name, type, direction, "
        "subject, body, date, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            app_id,
            contact_id,
            contact_name,
            data["type"],
            data["direction"],
            data.get("subject", ""),
            data["body"],
            data["date"],
            data.get("status", "sent"),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM communication WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row)


def load_communications(conn: DBConnection, app_id: int) -> list[dict[str, Any]]:
    """Load communications for an application, sorted by date desc."""
    rows = conn.execute(
        "SELECT * FROM communication WHERE app_id = ? ORDER BY date DESC, id DESC",
        (app_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def update_communication(
    conn: DBConnection, comm_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Update a communication. Returns updated communication."""
    row = conn.execute(
        "SELECT * FROM communication WHERE id = ?", (comm_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Communication {comm_id} not found")

    updatable = (
        "contact_id",
        "type",
        "direction",
        "subject",
        "body",
        "date",
        "status",
    )
    sets: list[str] = []
    params: list[Any] = []
    for field in updatable:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])

    # If contact_id changed, update contact_name too
    if "contact_id" in data and data["contact_id"] is not None:
        contact_row = conn.execute(
            "SELECT name FROM application_contact WHERE id = ?",
            (data["contact_id"],),
        ).fetchone()
        if contact_row:
            sets.append("contact_name = ?")
            params.append(contact_row["name"])

    if not sets:
        return dict(row)

    params.append(comm_id)
    conn.execute(
        f"UPDATE communication SET {', '.join(sets)} WHERE id = ?",
        params,
    )
    conn.commit()
    return dict(
        conn.execute("SELECT * FROM communication WHERE id = ?", (comm_id,)).fetchone()
    )


# --- Accomplishment operations ---


def _row_to_accomplishment(row: Any) -> dict[str, Any]:
    """Convert an accomplishment row to a dict with parsed tags."""
    return {
        "id": row["id"],
        "title": row["title"],
        "situation": row["situation"],
        "task": row["task"],
        "action": row["action"],
        "result": row["result"],
        "accomplishment_date": row["accomplishment_date"],
        "tags": json.loads(row["tags"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _row_to_accomplishment_summary(row: Any) -> dict[str, Any]:
    """Convert an accomplishment row to a summary dict (no STAR body)."""
    return {
        "id": row["id"],
        "title": row["title"],
        "accomplishment_date": row["accomplishment_date"],
        "tags": json.loads(row["tags"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_accomplishment(conn: DBConnection, data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new accomplishment row and return it."""
    cursor = conn.execute(
        "INSERT INTO accomplishment "
        "(title, situation, task, action, result, accomplishment_date, tags) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data["title"],
            data.get("situation", ""),
            data.get("task", ""),
            data.get("action", ""),
            data.get("result", ""),
            data.get("accomplishment_date"),
            json.dumps(data.get("tags", [])),
        ),
    )
    conn.commit()
    return load_accomplishment(conn, cursor.lastrowid)


def load_accomplishment(conn: DBConnection, acc_id: int) -> dict[str, Any]:
    """Load a single accomplishment by ID. Raises ValueError if not found."""
    row = conn.execute(
        "SELECT * FROM accomplishment WHERE id = ?", (acc_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Accomplishment {acc_id} not found")
    return _row_to_accomplishment(row)


def load_accomplishments(
    conn: DBConnection,
    tag: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    """List accomplishments ordered reverse-chronologically with optional filters.

    Args:
        tag: Filter by exact tag match (substring in JSON array).
        q: Case-insensitive substring search across title and STAR fields.
    """
    query = (
        "SELECT id, title, accomplishment_date, tags, created_at, updated_at "
        "FROM accomplishment"
    )
    conditions: list[str] = []
    params: list[Any] = []

    if tag:
        conditions.append("tags LIKE ?")
        params.append(f'%"{tag}"%')
    if q:
        pattern = f"%{q.lower()}%"
        conditions.append(
            "(LOWER(title) LIKE ? OR LOWER(situation) LIKE ? "
            "OR LOWER(task) LIKE ? OR LOWER(action) LIKE ? OR LOWER(result) LIKE ?)"
        )
        params.extend([pattern, pattern, pattern, pattern, pattern])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += (
        " ORDER BY "
        "CASE WHEN accomplishment_date IS NULL THEN 1 ELSE 0 END, "
        "accomplishment_date DESC, "
        "created_at DESC"
    )

    rows = conn.execute(query, params).fetchall()
    return [_row_to_accomplishment_summary(row) for row in rows]


def update_accomplishment(
    conn: DBConnection, acc_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Patch an accomplishment with provided fields. Raises ValueError if not found."""
    # Verify exists first
    load_accomplishment(conn, acc_id)

    updatable = (
        "title",
        "situation",
        "task",
        "action",
        "result",
        "accomplishment_date",
    )
    sets: list[str] = []
    params: list[Any] = []

    for field in updatable:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])

    if "tags" in data:
        sets.append("tags = ?")
        params.append(json.dumps(data["tags"]))

    if not sets:
        return load_accomplishment(conn, acc_id)

    sets.append("updated_at = datetime('now')")
    params.append(acc_id)

    conn.execute(
        f"UPDATE accomplishment SET {', '.join(sets)} WHERE id = ?",
        params,
    )
    conn.commit()
    return load_accomplishment(conn, acc_id)


def delete_accomplishment(conn: DBConnection, acc_id: int) -> dict[str, Any]:
    """Delete an accomplishment. Returns the deleted row. ValueError if not found."""
    acc = load_accomplishment(conn, acc_id)
    conn.execute("DELETE FROM accomplishment WHERE id = ?", (acc_id,))
    conn.commit()
    return acc


def load_accomplishment_tags(conn: DBConnection) -> list[str]:
    """Return a sorted unique list of all tags across all accomplishments."""
    rows = conn.execute("SELECT tags FROM accomplishment").fetchall()
    all_tags: set[str] = set()
    for row in rows:
        tags = json.loads(row["tags"])
        all_tags.update(tags)
    return sorted(all_tags)


def delete_communication(conn: DBConnection, comm_id: int) -> str:
    """Delete a communication. Returns its subject."""
    row = conn.execute(
        "SELECT * FROM communication WHERE id = ?", (comm_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Communication {comm_id} not found")

    subject = row["subject"] or "(no subject)"
    conn.execute("DELETE FROM communication WHERE id = ?", (comm_id,))
    conn.commit()
    return subject
