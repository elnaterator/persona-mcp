"""Unit tests for persona.migrations module (PostgreSQL).

Uses a self-contained module-scoped testcontainers fixture — no conftest.py
dependency — so these tests can run before conftest.py is rewritten.

Isolation strategy: module-scoped container (starts once) + function-scoped
pg_conn that creates a fresh PostgreSQL schema per test and drops it on teardown.
This avoids DDL leakage between tests without restarting the container.
"""

import uuid
from typing import Any, cast

import psycopg
import pytest
from psycopg.rows import dict_row
from testcontainers.postgres import PostgresContainer

# ---------------------------------------------------------------------------
# Module-scoped inline fixture: starts one container for all migration tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pg_dsn():
    """Start a postgres:16-alpine container and yield the connection DSN."""
    with PostgresContainer("postgres:16-alpine", driver=None) as container:
        yield container.get_connection_url()


@pytest.fixture
def pg_conn(pg_dsn: str):
    """Per-test isolated connection using a fresh PostgreSQL schema.

    Creates a unique schema, sets search_path to it, yields the connection,
    then drops the schema (and all its objects) on teardown.
    """
    schema = f"t_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(pg_dsn, row_factory=dict_row) as _raw_conn:  # type: ignore[call-overload]
        conn = cast(psycopg.Connection[Any], _raw_conn)
        conn.execute(f'CREATE SCHEMA "{schema}"')  # type: ignore[arg-type]
        conn.execute(f'SET search_path = "{schema}"')  # type: ignore[arg-type]
        conn.commit()
        yield conn
        conn.execute("SET search_path = public")
        conn.execute(f'DROP SCHEMA "{schema}" CASCADE')  # type: ignore[arg-type]
        conn.commit()


# ---------------------------------------------------------------------------
# Helper: get current schema version
# ---------------------------------------------------------------------------


def _get_version(conn) -> int:
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if row is None:
        return -1
    return row["version"] if isinstance(row, dict) else row[0]


# ---------------------------------------------------------------------------
# TestApplyMigrations
# ---------------------------------------------------------------------------


class TestApplyMigrations:
    """Tests for the migration framework."""

    def test_applies_all_migrations(self, pg_conn) -> None:
        from persona.migrations import SCHEMA_VERSION, apply_migrations

        apply_migrations(pg_conn)
        version = _get_version(pg_conn)
        assert version == SCHEMA_VERSION

    def test_no_op_when_already_current(self, pg_conn) -> None:
        from persona.migrations import apply_migrations

        apply_migrations(pg_conn)
        version_before = _get_version(pg_conn)

        # Apply again — should be a no-op
        apply_migrations(pg_conn)
        version_after = _get_version(pg_conn)

        assert version_before == version_after

    def test_raises_schema_version_error_when_db_ahead(self, pg_conn) -> None:
        from persona.migrations import SchemaVersionError, apply_migrations

        # Bootstrap schema_version table manually with a future version
        pg_conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version "
            "(version INTEGER NOT NULL DEFAULT 0)"
        )
        pg_conn.execute("DELETE FROM schema_version")
        pg_conn.execute("INSERT INTO schema_version (version) VALUES (999)")
        pg_conn.commit()

        with pytest.raises(SchemaVersionError):
            apply_migrations(pg_conn)

    def test_schema_version_error_has_versions(self) -> None:
        from persona.migrations import SchemaVersionError

        err = SchemaVersionError(db_version=5, code_version=1)
        assert err.db_version == 5
        assert err.code_version == 1
        assert "5" in str(err)
        assert "1" in str(err)

    def test_migration_error_has_context(self) -> None:
        from persona.migrations import MigrationError

        cause = RuntimeError("bad sql")
        err = MigrationError(from_version=0, to_version=1, cause=cause)
        assert err.from_version == 0
        assert err.to_version == 1
        assert err.__cause__ is cause or "bad sql" in str(err)

    def test_rollback_on_migration_failure(self, pg_conn) -> None:
        """A failed migration should leave the DB at the pre-migration version."""
        from persona.migrations import (
            MIGRATIONS,
            MigrationError,
            apply_migrations,
        )

        apply_migrations(pg_conn)
        version_before = _get_version(pg_conn)

        def broken_migration(c) -> None:
            raise RuntimeError("intentional failure")

        original_migrations = MIGRATIONS.copy()
        MIGRATIONS.append(broken_migration)

        try:
            with pytest.raises(MigrationError):
                apply_migrations(pg_conn)

            version_after = _get_version(pg_conn)
            assert version_after == version_before
        finally:
            MIGRATIONS.clear()
            MIGRATIONS.extend(original_migrations)

    def test_schema_version_bootstrapped_on_first_run(self, pg_conn) -> None:
        """schema_version must exist with exactly one row after apply_migrations."""
        from persona.migrations import apply_migrations

        apply_migrations(pg_conn)
        rows = pg_conn.execute("SELECT version FROM schema_version").fetchall()
        assert len(rows) == 1
        assert rows[0]["version"] >= 0


# ---------------------------------------------------------------------------
# Test individual migration final schema state
# ---------------------------------------------------------------------------


class TestMigrationV0ToV1:
    """Verify final schema state after v0→v1 migration."""

    def test_creates_all_v1_tables(self, pg_conn) -> None:
        from persona.migrations import migrate_v0_to_v1

        # Bootstrap schema_version first
        pg_conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version "
            "(version INTEGER NOT NULL DEFAULT 0)"
        )
        pg_conn.execute(
            "INSERT INTO schema_version (version) VALUES (0) ON CONFLICT DO NOTHING"
        )
        pg_conn.commit()

        migrate_v0_to_v1(pg_conn)

        tables = {
            row["tablename"]
            for row in pg_conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
            ).fetchall()
        }
        assert "contact" in tables
        assert "summary" in tables
        assert "experience" in tables
        assert "education" in tables
        assert "skill" in tables


class TestFullMigrationChain:
    """Tests for complete migration chain applied via apply_migrations."""

    def test_final_schema_has_users_table(self, pg_conn) -> None:
        from persona.migrations import apply_migrations

        apply_migrations(pg_conn)

        tables = {
            row["tablename"]
            for row in pg_conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
            ).fetchall()
        }
        assert "users" in tables
        assert "resume_version" in tables
        assert "application" in tables
        assert "accomplishment" in tables

    def test_resume_version_has_serial_pk(self, pg_conn) -> None:
        """After full migration, SERIAL PK on resume_version must be auto-assigned."""
        from persona.migrations import apply_migrations

        apply_migrations(pg_conn)

        pg_conn.execute("INSERT INTO users (id) VALUES ('test-user-serial')")
        pg_conn.execute(
            "INSERT INTO resume_version (user_id, label, resume_data) "
            "VALUES ('test-user-serial', 'Test', '{}')"
        )
        pg_conn.commit()

        row = pg_conn.execute(
            "SELECT id FROM resume_version WHERE user_id = 'test-user-serial'"
        ).fetchone()
        assert row is not None
        assert isinstance(row["id"], int)
        assert row["id"] > 0

    def test_version_incremented_through_full_chain(self, pg_conn) -> None:
        from persona.migrations import SCHEMA_VERSION, apply_migrations

        apply_migrations(pg_conn)
        version = _get_version(pg_conn)
        assert version == SCHEMA_VERSION
