"""PostgreSQL database operations for persona resume data."""

import datetime
import json
import logging
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from persona.db import DBConnection
from persona.migrations import apply_migrations

logger = logging.getLogger("persona")


def init_pool(dsn: str, min_size: int = 1, max_size: int = 10) -> ConnectionPool[Any]:
    """Initialize a PostgreSQL connection pool and run pending migrations.

    Opens a pool configured with dict_row, applies any pending schema
    migrations using a single connection checkout, and returns the pool
    ready for use.
    """
    pool = ConnectionPool(
        dsn,
        min_size=min_size,
        max_size=max_size,
        open=True,
        kwargs={"row_factory": dict_row},
    )
    with pool.connection() as conn:
        apply_migrations(conn)
    logger.info("PostgreSQL pool initialized (min=%d, max=%d)", min_size, max_size)
    return pool


# --- User operations ---


def upsert_user(
    conn: DBConnection,
    user_id: str,
    email: str | None,
    display_name: str | None,
) -> None:
    """Insert or update a user row. Called on each successful sign-in."""
    conn.execute(
        """
        INSERT INTO users (id, email, display_name)
        VALUES (%s, %s, %s)
        ON CONFLICT(id) DO UPDATE SET
            email        = excluded.email,
            display_name = excluded.display_name
        """,
        (user_id, email, display_name),
    )


def delete_user(conn: DBConnection, user_id: str) -> None:
    """Hard-delete a user and all their owned data (cascade via FK)."""
    conn.execute("DELETE FROM users WHERE id = %s", (user_id,))


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
    conn: DBConnection,
    label: str,
    resume_data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Create a new resume version. Returns the created version."""
    effective_uid = user_id or "legacy"
    data_json = json.dumps(resume_data)
    row = conn.execute(
        "INSERT INTO resume_version (user_id, label, is_default, resume_data) "
        "VALUES (%s, %s, 0, %s) RETURNING id",
        (effective_uid, label, data_json),
    ).fetchone()
    new_id = row["id"]
    result_row = conn.execute(
        "SELECT * FROM resume_version WHERE id = %s",
        (new_id,),
    ).fetchone()
    return _row_to_resume_data(result_row)


def load_resume_version(
    conn: DBConnection,
    version_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Load a resume version by ID. Raises ValueError if not found."""
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = %s", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(
            f"Resume version {version_id} belongs to a different user"
        )
    return _row_to_resume_data(row)


def load_resume_versions(
    conn: DBConnection,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Load all resume versions with metadata and app_count."""
    query = (
        "SELECT rv.id, rv.label, rv.is_default, rv.created_at, rv.updated_at, "
        "COUNT(a.id) AS app_count "
        "FROM resume_version rv "
        "LEFT JOIN application a ON a.resume_version_id = rv.id"
    )
    params: list[Any] = []

    if user_id is not None:
        query += " WHERE rv.user_id = %s"
        params.append(user_id)

    query += " GROUP BY rv.id ORDER BY rv.id"

    rows = conn.execute(query, params).fetchall()
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


def load_default_resume_version(
    conn: DBConnection,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Load the default resume version. Raises ValueError if none."""
    if user_id is not None:
        row = conn.execute(
            "SELECT * FROM resume_version WHERE user_id = %s AND is_default = 1",
            (user_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM resume_version WHERE is_default = 1"
        ).fetchone()

    if row is None:
        raise ValueError("No default resume version found")
    return _row_to_resume_data(row)


def update_resume_version_metadata(
    conn: DBConnection,
    version_id: int,
    label: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Update resume version label. Returns updated version."""
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = %s", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(
            f"Resume version {version_id} belongs to a different user"
        )

    conn.execute(
        "UPDATE resume_version SET label = %s, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s",
        (label, version_id),
    )
    return load_resume_version(conn, version_id)


def update_resume_version_data(
    conn: DBConnection,
    version_id: int,
    resume_data: dict[str, Any],
    user_id: str | None = None,
) -> None:
    """Update the resume_data JSON blob for a version."""
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = %s", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(
            f"Resume version {version_id} belongs to a different user"
        )

    conn.execute(
        "UPDATE resume_version "
        "SET resume_data = %s, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s",
        (json.dumps(resume_data), version_id),
    )


def delete_resume_version(
    conn: DBConnection,
    version_id: int,
    user_id: str | None = None,
) -> str:
    """Delete a resume version. Returns label of deleted version.

    If deleting the default and other versions exist, auto-promotes
    the most recently updated version. Rejects deleting the last version.
    """
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = %s", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(
            f"Resume version {version_id} belongs to a different user"
        )

    label = row["label"]
    is_default = bool(row["is_default"])

    if user_id is not None:
        count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM resume_version WHERE user_id = %s",
            (user_id,),
        ).fetchone()["cnt"]
    else:
        count = conn.execute("SELECT COUNT(*) AS cnt FROM resume_version").fetchone()[
            "cnt"
        ]

    if count <= 1:
        raise ValueError("Cannot delete the last remaining resume version")

    conn.execute("SAVEPOINT delete_and_promote")
    try:
        conn.execute("DELETE FROM resume_version WHERE id = %s", (version_id,))

        if is_default:
            if user_id is not None:
                conn.execute(
                    "UPDATE resume_version SET is_default = 1 "
                    "WHERE id = ("
                    "  SELECT id FROM resume_version "
                    "  WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1"
                    ")",
                    (user_id,),
                )
            else:
                conn.execute(
                    "UPDATE resume_version SET is_default = 1 "
                    "WHERE id = ("
                    "  SELECT id FROM resume_version "
                    "  ORDER BY updated_at DESC LIMIT 1"
                    ")"
                )

    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT delete_and_promote")
        raise
    conn.execute("RELEASE SAVEPOINT delete_and_promote")
    return label


def set_default_resume_version(
    conn: DBConnection,
    version_id: int,
    user_id: str | None = None,
) -> str:
    """Set a resume version as default. Returns its label."""
    row = conn.execute(
        "SELECT * FROM resume_version WHERE id = %s", (version_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Resume version {version_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(
            f"Resume version {version_id} belongs to a different user"
        )

    label = row["label"]

    if user_id is not None:
        conn.execute(
            "UPDATE resume_version "
            "SET is_default = CASE WHEN id = %s THEN 1 ELSE 0 END "
            "WHERE user_id = %s",
            (version_id, user_id),
        )
    else:
        conn.execute(
            "UPDATE resume_version "
            "SET is_default = CASE WHEN id = %s THEN 1 ELSE 0 END",
            (version_id,),
        )
    return label


# --- Application operations ---


def create_application(
    conn: DBConnection,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Create a new application. Returns the created application."""
    effective_uid = user_id or "legacy"
    row = conn.execute(
        "INSERT INTO application "
        "(user_id, company, position, description, status, url, notes, "
        "resume_version_id) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (
            effective_uid,
            data["company"],
            data["position"],
            data.get("description", ""),
            data.get("status", "Interested"),
            data.get("url"),
            data.get("notes", ""),
            data.get("resume_version_id"),
        ),
    ).fetchone()
    return load_application(conn, row["id"])


def load_application(
    conn: DBConnection,
    app_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Load a single application by ID."""
    row = conn.execute("SELECT * FROM application WHERE id = %s", (app_id,)).fetchone()
    if row is None:
        raise ValueError(f"Application {app_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(f"Application {app_id} belongs to a different user")
    return dict(row)


def load_applications(
    conn: DBConnection,
    status: str | None = None,
    q: str | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Load applications with optional status filter and search."""
    query = (
        "SELECT id, company, position, status, url, "
        "resume_version_id, created_at, updated_at "
        "FROM application"
    )
    conditions: list[str] = []
    params: list[Any] = []

    if user_id is not None:
        conditions.append("user_id = %s")
        params.append(user_id)
    if status:
        conditions.append("status = %s")
        params.append(status)
    if q:
        conditions.append("(company ILIKE %s OR position ILIKE %s)")
        pattern = f"%{q}%"
        params.extend([pattern, pattern])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY updated_at DESC"

    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def update_application(
    conn: DBConnection,
    app_id: int,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Update application fields. Returns updated application."""
    existing = load_application(conn, app_id, user_id=user_id)

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
            sets.append(f"{field} = %s")
            params.append(data[field])

    if not sets:
        return existing

    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(app_id)

    conn.execute(
        f"UPDATE application SET {', '.join(sets)} WHERE id = %s",
        params,
    )
    return load_application(conn, app_id)


def delete_application(
    conn: DBConnection,
    app_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Delete an application and cascade. Returns deleted app data."""
    app = load_application(conn, app_id, user_id=user_id)
    conn.execute("DELETE FROM application WHERE id = %s", (app_id,))
    return app


# --- Application Contact operations ---


def create_contact(
    conn: DBConnection, app_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Create a contact for an application."""
    load_application(conn, app_id)

    row = conn.execute(
        "INSERT INTO application_contact "
        "(app_id, name, role, email, phone, notes) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (
            app_id,
            data["name"],
            data.get("role"),
            data.get("email"),
            data.get("phone"),
            data.get("notes", ""),
        ),
    ).fetchone()
    result_row = conn.execute(
        "SELECT * FROM application_contact WHERE id = %s",
        (row["id"],),
    ).fetchone()
    return dict(result_row)


def load_contacts(conn: DBConnection, app_id: int) -> list[dict[str, Any]]:
    """Load all contacts for an application."""
    rows = conn.execute(
        "SELECT * FROM application_contact WHERE app_id = %s ORDER BY id",
        (app_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def update_contact(
    conn: DBConnection, contact_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Update a contact. Returns updated contact."""
    row = conn.execute(
        "SELECT * FROM application_contact WHERE id = %s",
        (contact_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Contact {contact_id} not found")

    updatable = ("name", "role", "email", "phone", "notes")
    sets: list[str] = []
    params: list[Any] = []
    for field in updatable:
        if field in data:
            sets.append(f"{field} = %s")
            params.append(data[field])

    if not sets:
        return dict(row)

    params.append(contact_id)
    conn.execute(
        f"UPDATE application_contact SET {', '.join(sets)} WHERE id = %s",
        params,
    )
    return dict(
        conn.execute(
            "SELECT * FROM application_contact WHERE id = %s",
            (contact_id,),
        ).fetchone()
    )


def delete_contact(conn: DBConnection, contact_id: int) -> str:
    """Delete a contact. Returns contact name."""
    row = conn.execute(
        "SELECT * FROM application_contact WHERE id = %s",
        (contact_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Contact {contact_id} not found")

    name = row["name"]
    conn.execute("DELETE FROM application_contact WHERE id = %s", (contact_id,))
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
            "SELECT name FROM application_contact WHERE id = %s",
            (contact_id,),
        ).fetchone()
        if contact_row:
            contact_name = contact_row["name"]

    row = conn.execute(
        "INSERT INTO communication "
        "(app_id, contact_id, contact_name, type, direction, "
        "subject, body, date, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
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
    ).fetchone()
    result_row = conn.execute(
        "SELECT * FROM communication WHERE id = %s",
        (row["id"],),
    ).fetchone()
    return dict(result_row)


def load_communications(conn: DBConnection, app_id: int) -> list[dict[str, Any]]:
    """Load communications for an application, sorted by date desc."""
    rows = conn.execute(
        "SELECT * FROM communication WHERE app_id = %s ORDER BY date DESC, id DESC",
        (app_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def update_communication(
    conn: DBConnection, comm_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Update a communication. Returns updated communication."""
    row = conn.execute(
        "SELECT * FROM communication WHERE id = %s", (comm_id,)
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
            sets.append(f"{field} = %s")
            params.append(data[field])

    if "contact_id" in data and data["contact_id"] is not None:
        contact_row = conn.execute(
            "SELECT name FROM application_contact WHERE id = %s",
            (data["contact_id"],),
        ).fetchone()
        if contact_row:
            sets.append("contact_name = %s")
            params.append(contact_row["name"])

    if not sets:
        return dict(row)

    params.append(comm_id)
    conn.execute(
        f"UPDATE communication SET {', '.join(sets)} WHERE id = %s",
        params,
    )
    return dict(
        conn.execute("SELECT * FROM communication WHERE id = %s", (comm_id,)).fetchone()
    )


# --- Accomplishment operations ---


def _dt(value: Any) -> Any:
    """Return ISO string if value is a datetime/date, otherwise return as-is."""
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return value


def _row_to_accomplishment(row: Any) -> dict[str, Any]:
    """Convert an accomplishment row to a dict with parsed tags."""
    return {
        "id": row["id"],
        "title": row["title"],
        "situation": row["situation"],
        "task": row["task"],
        "action": row["action"],
        "result": row["result"],
        "accomplishment_date": _dt(row["accomplishment_date"]),
        "tags": json.loads(row["tags"]),
        "created_at": _dt(row["created_at"]),
        "updated_at": _dt(row["updated_at"]),
    }


def _row_to_accomplishment_summary(row: Any) -> dict[str, Any]:
    """Convert an accomplishment row to a summary dict (no STAR body)."""
    return {
        "id": row["id"],
        "title": row["title"],
        "accomplishment_date": _dt(row["accomplishment_date"]),
        "tags": json.loads(row["tags"]),
        "created_at": _dt(row["created_at"]),
        "updated_at": _dt(row["updated_at"]),
    }


def create_accomplishment(
    conn: DBConnection,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Insert a new accomplishment row and return it."""
    effective_uid = user_id or "legacy"
    row = conn.execute(
        "INSERT INTO accomplishment "
        "(user_id, title, situation, task, action, result, accomplishment_date, tags) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (
            effective_uid,
            data["title"],
            data.get("situation", ""),
            data.get("task", ""),
            data.get("action", ""),
            data.get("result", ""),
            data.get("accomplishment_date"),
            json.dumps(data.get("tags", [])),
        ),
    ).fetchone()
    return load_accomplishment(conn, row["id"])


def load_accomplishment(
    conn: DBConnection,
    acc_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Load a single accomplishment by ID. Raises ValueError if not found."""
    row = conn.execute(
        "SELECT * FROM accomplishment WHERE id = %s", (acc_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Accomplishment {acc_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(f"Accomplishment {acc_id} belongs to a different user")
    return _row_to_accomplishment(row)


def load_accomplishments(
    conn: DBConnection,
    tag: str | None = None,
    q: str | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """List accomplishments ordered reverse-chronologically with optional filters."""
    query = (
        "SELECT id, title, accomplishment_date, tags, created_at, updated_at "
        "FROM accomplishment"
    )
    conditions: list[str] = []
    params: list[Any] = []

    if user_id is not None:
        conditions.append("user_id = %s")
        params.append(user_id)
    if tag:
        conditions.append("tags ILIKE %s")
        params.append(f'%"{tag}"%')
    if q:
        pattern = f"%{q}%"
        conditions.append(
            "(title ILIKE %s OR situation ILIKE %s "
            "OR task ILIKE %s OR action ILIKE %s OR result ILIKE %s)"
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
    conn: DBConnection,
    acc_id: int,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Patch an accomplishment with provided fields. Raises ValueError if not found."""
    load_accomplishment(conn, acc_id, user_id=user_id)

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
            sets.append(f"{field} = %s")
            params.append(data[field])

    if "tags" in data:
        sets.append("tags = %s")
        params.append(json.dumps(data["tags"]))

    if not sets:
        return load_accomplishment(conn, acc_id)

    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(acc_id)

    conn.execute(
        f"UPDATE accomplishment SET {', '.join(sets)} WHERE id = %s",
        params,
    )
    return load_accomplishment(conn, acc_id)


def delete_accomplishment(
    conn: DBConnection,
    acc_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Delete an accomplishment. Returns the deleted row. ValueError if not found."""
    acc = load_accomplishment(conn, acc_id, user_id=user_id)
    conn.execute("DELETE FROM accomplishment WHERE id = %s", (acc_id,))
    return acc


def load_accomplishment_tags(
    conn: DBConnection,
    user_id: str | None = None,
) -> list[str]:
    """Return a sorted unique list of all tags across all accomplishments."""
    if user_id is not None:
        rows = conn.execute(
            "SELECT tags FROM accomplishment WHERE user_id = %s", (user_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT tags FROM accomplishment").fetchall()
    all_tags: set[str] = set()
    for row in rows:
        tags = json.loads(row["tags"])
        all_tags.update(tags)
    return sorted(all_tags)


# --- Note operations ---


def _row_to_note(row: Any) -> dict[str, Any]:
    """Full note with content."""
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "content": row["content"],
        "tags": json.loads(row["tags"]),
        "created_at": _dt(row["created_at"]),
        "updated_at": _dt(row["updated_at"]),
    }


def _row_to_note_summary(row: Any) -> dict[str, Any]:
    """Summary for list view (content omitted)."""
    return {
        "id": row["id"],
        "title": row["title"],
        "tags": json.loads(row["tags"]),
        "created_at": _dt(row["created_at"]),
        "updated_at": _dt(row["updated_at"]),
    }


def create_note(
    conn: DBConnection,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Insert a new note row and return it."""
    effective_uid = user_id or "legacy"
    row = conn.execute(
        "INSERT INTO note "
        "(user_id, title, content, tags) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (
            effective_uid,
            data["title"],
            data.get("content", ""),
            json.dumps(data.get("tags", [])),
        ),
    ).fetchone()
    return load_note(conn, row["id"])


def load_note(
    conn: DBConnection,
    note_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Load a single note by ID. Raises ValueError if not found."""
    row = conn.execute("SELECT * FROM note WHERE id = %s", (note_id,)).fetchone()
    if row is None:
        raise ValueError(f"Note {note_id} not found")
    if user_id is not None and row["user_id"] != user_id:
        raise PermissionError(f"Note {note_id} belongs to a different user")
    return _row_to_note(row)


def load_notes(
    conn: DBConnection,
    tag: str | None = None,
    q: str | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """List notes as summaries ordered by updated_at DESC."""
    query = "SELECT id, title, tags, created_at, updated_at FROM note"
    conditions: list[str] = []
    params: list[Any] = []

    if user_id is not None:
        conditions.append("user_id = %s")
        params.append(user_id)
    if tag:
        conditions.append("tags ILIKE %s")
        params.append(f'%"{tag}"%')
    if q:
        words = q.strip().split()
        for word in words:
            pattern = f"%{word}%"
            conditions.append("(title ILIKE %s OR content ILIKE %s)")
            params.extend([pattern, pattern])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY updated_at DESC"

    rows = conn.execute(query, params).fetchall()
    return [_row_to_note_summary(row) for row in rows]


def update_note(
    conn: DBConnection,
    note_id: int,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Patch a note with provided fields. Raises ValueError if not found."""
    load_note(conn, note_id, user_id=user_id)

    updatable = ("title", "content")
    sets: list[str] = []
    params: list[Any] = []

    for field in updatable:
        if field in data:
            sets.append(f"{field} = %s")
            params.append(data[field])

    if "tags" in data:
        sets.append("tags = %s")
        params.append(json.dumps(data["tags"]))

    if not sets:
        return load_note(conn, note_id)

    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(note_id)

    conn.execute(
        f"UPDATE note SET {', '.join(sets)} WHERE id = %s",
        params,
    )
    return load_note(conn, note_id)


def delete_note(
    conn: DBConnection,
    note_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Delete a note. Returns the deleted row. ValueError if not found."""
    note = load_note(conn, note_id, user_id=user_id)
    conn.execute("DELETE FROM note WHERE id = %s", (note_id,))
    return note


def load_note_tags(
    conn: DBConnection,
    user_id: str | None = None,
) -> list[str]:
    """Return a sorted unique list of all tags across all notes."""
    if user_id is not None:
        rows = conn.execute(
            "SELECT tags FROM note WHERE user_id = %s", (user_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT tags FROM note").fetchall()
    all_tags: set[str] = set()
    for row in rows:
        tags = json.loads(row["tags"])
        all_tags.update(tags)
    return sorted(all_tags)


def delete_communication(conn: DBConnection, comm_id: int) -> str:
    """Delete a communication. Returns its subject."""
    row = conn.execute(
        "SELECT * FROM communication WHERE id = %s", (comm_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Communication {comm_id} not found")

    subject = row["subject"] or "(no subject)"
    conn.execute("DELETE FROM communication WHERE id = %s", (comm_id,))
    return subject
