"""Schema migration framework using PRAGMA user_version."""

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


MIGRATIONS: list = [
    migrate_v0_to_v1,
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
