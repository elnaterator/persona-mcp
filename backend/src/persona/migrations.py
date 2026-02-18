"""Schema migration framework using PRAGMA user_version."""

import json
import logging
import sqlite3

logger = logging.getLogger("persona")


class SchemaVersionError(Exception):
    """Database schema version is newer than code supports."""

    def __init__(self, db_version: int, code_version: int) -> None:
        self.db_version = db_version
        self.code_version = code_version
        super().__init__(
            f"Database schema version {db_version} is newer than "
            f"code version {code_version}. Please upgrade the application."
        )


class MigrationError(Exception):
    """A schema migration failed."""

    def __init__(self, from_version: int, to_version: int, cause: Exception) -> None:
        self.from_version = from_version
        self.to_version = to_version
        super().__init__(
            f"Migration from version {from_version} to {to_version} failed: {cause}"
        )
        self.__cause__ = cause


def migrate_v0_to_v1(conn: sqlite3.Connection) -> None:
    """Initial schema: create all tables."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            linkedin TEXT,
            website TEXT,
            github TEXT
        );

        CREATE TABLE IF NOT EXISTS summary (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            text TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            location TEXT,
            highlights TEXT NOT NULL DEFAULT '[]',
            position INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution TEXT NOT NULL,
            degree TEXT NOT NULL,
            field TEXT,
            start_date TEXT,
            end_date TEXT,
            honors TEXT,
            position INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS skill (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'Other'
        );
    """)


def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Replace singleton resume tables with resume_version + application tables."""
    conn.execute("PRAGMA foreign_keys = OFF")

    # Create new tables
    conn.executescript("""
        CREATE TABLE resume_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            is_default INTEGER NOT NULL DEFAULT 0,
            resume_data TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE application (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Interested',
            url TEXT,
            notes TEXT NOT NULL DEFAULT '',
            resume_version_id INTEGER REFERENCES resume_version(id)
                ON DELETE SET NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE application_contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL REFERENCES application(id)
                ON DELETE CASCADE,
            name TEXT NOT NULL,
            role TEXT,
            email TEXT,
            phone TEXT,
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE communication (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL REFERENCES application(id)
                ON DELETE CASCADE,
            contact_id INTEGER REFERENCES application_contact(id)
                ON DELETE SET NULL,
            contact_name TEXT,
            type TEXT NOT NULL,
            direction TEXT NOT NULL,
            subject TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'sent',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX idx_application_status
            ON application(status);
        CREATE INDEX idx_application_updated
            ON application(updated_at DESC);
        CREATE INDEX idx_application_contact_app
            ON application_contact(app_id);
        CREATE INDEX idx_communication_app
            ON communication(app_id);
        CREATE INDEX idx_communication_date
            ON communication(date DESC);
        CREATE INDEX idx_resume_version_default
            ON resume_version(is_default) WHERE is_default = 1;
    """)

    # Migrate existing resume data into default version
    resume_data: dict = {
        "contact": {},
        "summary": "",
        "experience": [],
        "education": [],
        "skills": [],
    }

    # Read contact
    row = conn.execute("SELECT * FROM contact WHERE id = 1").fetchone()
    if row:
        contact = {}
        contact_keys = (
            "name",
            "email",
            "phone",
            "location",
            "linkedin",
            "website",
            "github",
        )
        for key in contact_keys:
            contact[key] = row[key]
        resume_data["contact"] = contact

    # Read summary
    row = conn.execute("SELECT text FROM summary WHERE id = 1").fetchone()
    if row:
        resume_data["summary"] = row[0] or ""

    # Read experience
    rows = conn.execute("SELECT * FROM experience ORDER BY position").fetchall()
    for row in rows:
        resume_data["experience"].append(
            {
                "title": row["title"],
                "company": row["company"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "location": row["location"],
                "highlights": json.loads(row["highlights"]),
            }
        )

    # Read education
    rows = conn.execute("SELECT * FROM education ORDER BY position").fetchall()
    for row in rows:
        resume_data["education"].append(
            {
                "institution": row["institution"],
                "degree": row["degree"],
                "field": row["field"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "honors": row["honors"],
            }
        )

    # Read skills
    rows = conn.execute("SELECT * FROM skill ORDER BY id").fetchall()
    for row in rows:
        resume_data["skills"].append({"name": row["name"], "category": row["category"]})

    # Insert default resume version
    conn.execute(
        "INSERT INTO resume_version (label, is_default, resume_data) VALUES (?, 1, ?)",
        ("Default Resume", json.dumps(resume_data)),
    )

    # Drop old tables
    conn.executescript("""
        DROP TABLE IF EXISTS skill;
        DROP TABLE IF EXISTS education;
        DROP TABLE IF EXISTS experience;
        DROP TABLE IF EXISTS summary;
        DROP TABLE IF EXISTS contact;
    """)

    conn.execute("PRAGMA foreign_keys = ON")


MIGRATIONS: list = [
    migrate_v0_to_v1,
    migrate_v1_to_v2,
]

SCHEMA_VERSION: int = len(MIGRATIONS)


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply pending migrations to bring the database to the current schema version."""
    current = conn.execute("PRAGMA user_version").fetchone()[0]

    if current > len(MIGRATIONS):
        raise SchemaVersionError(db_version=current, code_version=len(MIGRATIONS))

    if current == len(MIGRATIONS):
        logger.info("Database schema is current (version %d)", current)
        return

    for i in range(current, len(MIGRATIONS)):
        target = i + 1
        logger.info("Applying migration v%d → v%d", i, target)
        try:
            MIGRATIONS[i](conn)
            conn.execute(f"PRAGMA user_version = {target}")
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise MigrationError(from_version=i, to_version=target, cause=e) from e

    logger.info("Database migrated to version %d", len(MIGRATIONS))
