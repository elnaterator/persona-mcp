"""Schema migration framework using schema_version table (PostgreSQL)."""

import json
import logging

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


def _bootstrap_schema_version(conn) -> None:
    """Create schema_version table if it doesn't exist and seed with version 0."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        "INSERT INTO schema_version (version) VALUES (0) ON CONFLICT DO NOTHING"
    )
    # If table was just created but INSERT above didn't fire (table already had rows),
    # ensure there is exactly one row by inserting only when empty.
    row = conn.execute("SELECT COUNT(*) AS cnt FROM schema_version").fetchone()
    count = row["cnt"] if isinstance(row, dict) else row[0]
    if count == 0:
        conn.execute("INSERT INTO schema_version (version) VALUES (0)")
    conn.commit()


def _get_version(conn) -> int:
    """Read current schema version."""
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if row is None:
        return 0
    return row["version"] if isinstance(row, dict) else row[0]


def migrate_v0_to_v1(conn) -> None:
    """Initial schema: create all tables."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            linkedin TEXT,
            website TEXT,
            github TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS summary (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            text TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS experience (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            location TEXT,
            highlights TEXT NOT NULL DEFAULT '[]',
            position INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS education (
            id SERIAL PRIMARY KEY,
            institution TEXT NOT NULL,
            degree TEXT NOT NULL,
            field TEXT,
            start_date TEXT,
            end_date TEXT,
            honors TEXT,
            position INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS skill (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'Other'
        )
        """
    )
    conn.execute(
        "UPDATE schema_version SET version = %s",
        (1,),
    )
    conn.commit()


def migrate_v1_to_v2(conn) -> None:
    """Replace singleton resume tables with resume_version + application tables."""
    conn.execute(
        """
        CREATE TABLE resume_version (
            id SERIAL PRIMARY KEY,
            label TEXT NOT NULL,
            is_default INTEGER NOT NULL DEFAULT 0,
            resume_data TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE application (
            id SERIAL PRIMARY KEY,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Interested',
            url TEXT,
            notes TEXT NOT NULL DEFAULT '',
            resume_version_id INTEGER REFERENCES resume_version(id)
                ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE application_contact (
            id SERIAL PRIMARY KEY,
            app_id INTEGER NOT NULL REFERENCES application(id)
                ON DELETE CASCADE,
            name TEXT NOT NULL,
            role TEXT,
            email TEXT,
            phone TEXT,
            notes TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE communication (
            id SERIAL PRIMARY KEY,
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
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("CREATE INDEX idx_application_status ON application(status)")
    conn.execute("CREATE INDEX idx_application_updated ON application(updated_at DESC)")
    conn.execute(
        "CREATE INDEX idx_application_contact_app ON application_contact(app_id)"
    )
    conn.execute("CREATE INDEX idx_communication_app ON communication(app_id)")
    conn.execute("CREATE INDEX idx_communication_date ON communication(date DESC)")
    conn.execute(
        "CREATE INDEX idx_resume_version_default "
        "ON resume_version(is_default) WHERE is_default = 1"
    )

    # Migrate existing resume data into default version
    resume_data: dict = {
        "contact": {},
        "summary": "",
        "experience": [],
        "education": [],
        "skills": [],
    }

    row = conn.execute("SELECT * FROM contact WHERE id = 1").fetchone()
    if row:
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
            resume_data["contact"][key] = row[key]

    row = conn.execute("SELECT text FROM summary WHERE id = 1").fetchone()
    if row:
        resume_data["summary"] = row[0] or ""

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

    rows = conn.execute("SELECT * FROM skill ORDER BY id").fetchall()
    for row in rows:
        resume_data["skills"].append({"name": row["name"], "category": row["category"]})

    conn.execute(
        "INSERT INTO resume_version (label, is_default, resume_data) "
        "VALUES (%s, 1, %s)",
        ("Default Resume", json.dumps(resume_data)),
    )

    # Drop old tables
    conn.execute("DROP TABLE IF EXISTS skill CASCADE")
    conn.execute("DROP TABLE IF EXISTS education CASCADE")
    conn.execute("DROP TABLE IF EXISTS experience CASCADE")
    conn.execute("DROP TABLE IF EXISTS summary CASCADE")
    conn.execute("DROP TABLE IF EXISTS contact CASCADE")

    conn.execute("UPDATE schema_version SET version = %s", (2,))
    conn.commit()


def migrate_v2_to_v3(conn) -> None:
    """Add accomplishment table with STAR fields and tags."""
    conn.execute(
        """
        CREATE TABLE accomplishment (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            situation TEXT NOT NULL DEFAULT '',
            task TEXT NOT NULL DEFAULT '',
            action TEXT NOT NULL DEFAULT '',
            result TEXT NOT NULL DEFAULT '',
            accomplishment_date TEXT,
            tags TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX idx_accomplishment_date "
        "ON accomplishment(accomplishment_date DESC)"
    )
    conn.execute(
        "CREATE INDEX idx_accomplishment_created ON accomplishment(created_at DESC)"
    )
    conn.execute("UPDATE schema_version SET version = %s", (3,))
    conn.commit()


def migrate_v3_to_v4(conn) -> None:
    """Add users table and thread user_id FK into owned tables."""
    conn.execute(
        """
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT,
            display_name TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("INSERT INTO users (id) VALUES ('legacy')")

    # resume_version: add user_id column, backfill, add FK constraint
    conn.execute("ALTER TABLE resume_version ADD COLUMN user_id TEXT")
    conn.execute("UPDATE resume_version SET user_id = 'legacy'")
    conn.execute("ALTER TABLE resume_version ALTER COLUMN user_id SET NOT NULL")
    conn.execute(
        "ALTER TABLE resume_version ADD CONSTRAINT fk_rv_user "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    )

    # application: add user_id column, backfill, add FK constraint
    conn.execute("ALTER TABLE application ADD COLUMN user_id TEXT")
    conn.execute("UPDATE application SET user_id = 'legacy'")
    conn.execute("ALTER TABLE application ALTER COLUMN user_id SET NOT NULL")
    conn.execute(
        "ALTER TABLE application ADD CONSTRAINT fk_app_user "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    )

    # accomplishment: add user_id column, backfill, add FK constraint
    conn.execute("ALTER TABLE accomplishment ADD COLUMN user_id TEXT")
    conn.execute("UPDATE accomplishment SET user_id = 'legacy'")
    conn.execute("ALTER TABLE accomplishment ALTER COLUMN user_id SET NOT NULL")
    conn.execute(
        "ALTER TABLE accomplishment ADD CONSTRAINT fk_acc_user "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    )

    # Add new indexes
    conn.execute("CREATE INDEX idx_resume_version_user ON resume_version(user_id)")
    conn.execute(
        "CREATE INDEX idx_resume_version_user_default "
        "ON resume_version(user_id, is_default) WHERE is_default = 1"
    )
    conn.execute("CREATE INDEX idx_application_user ON application(user_id)")
    conn.execute("CREATE INDEX idx_accomplishment_user ON accomplishment(user_id)")

    conn.execute("UPDATE schema_version SET version = %s", (4,))
    conn.commit()


def migrate_v4_to_v5(conn) -> None:
    """Flatten items-based skills into individual flat skill entries.

    Prior to this migration, skills could be stored as:
      {"name": "Languages", "category": "Other", "items": ["Python", "TypeScript"]}

    After this migration, each skill has exactly one name and one category:
      {"name": "Python", "category": "Languages"}
      {"name": "TypeScript", "category": "Languages"}

    Skills with no items (or empty items) are preserved with the items field stripped.
    """
    rows = conn.execute("SELECT id, resume_data FROM resume_version").fetchall()
    for row in rows:
        version_id = row["id"] if isinstance(row, dict) else row[0]
        resume_data_str = row["resume_data"] if isinstance(row, dict) else row[1]
        resume_data = json.loads(resume_data_str)

        old_skills = resume_data.get("skills", [])
        new_skills: list[dict] = []
        for skill in old_skills:
            items = skill.get("items", [])
            if items:
                # Each item becomes a flat skill; the old name becomes the category
                category = skill.get("name", "Other")
                for item in items:
                    new_skills.append({"name": item, "category": category})
            else:
                # Keep as-is, strip the items field
                new_skills.append(
                    {"name": skill["name"], "category": skill.get("category", "Other")}
                )

        resume_data["skills"] = new_skills
        conn.execute(
            "UPDATE resume_version SET resume_data = %s WHERE id = %s",
            (json.dumps(resume_data), version_id),
        )

    conn.execute("UPDATE schema_version SET version = %s", (5,))
    conn.commit()


def migrate_v5_to_v6(conn) -> None:
    """Add note table for personal context notes."""
    conn.execute(
        """
        CREATE TABLE note (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT NOT NULL,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL DEFAULT '',
            tags        TEXT NOT NULL DEFAULT '[]',
            created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_note_user FOREIGN KEY (user_id)
                REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX idx_note_user ON note(user_id)")
    conn.execute("CREATE INDEX idx_note_updated ON note(updated_at DESC)")
    conn.execute("UPDATE schema_version SET version = %s", (6,))
    conn.commit()


MIGRATIONS: list = [
    migrate_v0_to_v1,
    migrate_v1_to_v2,
    migrate_v2_to_v3,
    migrate_v3_to_v4,
    migrate_v4_to_v5,
    migrate_v5_to_v6,
]

SCHEMA_VERSION: int = len(MIGRATIONS)


def apply_migrations(conn) -> None:
    """Apply pending migrations to bring the database to the current schema version."""
    _bootstrap_schema_version(conn)
    current = _get_version(conn)

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
        except Exception as e:
            conn.rollback()
            raise MigrationError(from_version=i, to_version=target, cause=e) from e

    logger.info("Database migrated to version %d", len(MIGRATIONS))
