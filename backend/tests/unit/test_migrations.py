"""Unit tests for persona.migrations module."""

import sqlite3

import pytest


class TestApplyMigrations:
    """Tests for the migration framework."""

    def test_applies_v0_to_v1_migration(self) -> None:
        from persona.migrations import SCHEMA_VERSION, apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)

        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == SCHEMA_VERSION
        assert version >= 1
        conn.close()

    def test_v0_to_v1_creates_all_tables(self) -> None:
        from persona.migrations import apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "contact" in tables
        assert "summary" in tables
        assert "experience" in tables
        assert "education" in tables
        assert "skill" in tables
        conn.close()

    def test_no_op_when_already_current(self) -> None:
        from persona.migrations import apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)
        version_before = conn.execute("PRAGMA user_version").fetchone()[0]

        # Apply again — should be a no-op
        apply_migrations(conn)
        version_after = conn.execute("PRAGMA user_version").fetchone()[0]

        assert version_before == version_after
        conn.close()

    def test_raises_schema_version_error_when_db_ahead(self) -> None:
        from persona.migrations import SchemaVersionError, apply_migrations

        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA user_version = 999")

        with pytest.raises(SchemaVersionError):
            apply_migrations(conn)
        conn.close()

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

    def test_rollback_on_migration_failure(self) -> None:
        """A failed migration should leave the DB at the pre-migration version."""
        from persona.migrations import (
            MIGRATIONS,
            MigrationError,
            apply_migrations,
        )

        conn = sqlite3.connect(":memory:")

        # First, apply real migrations to get to current version
        apply_migrations(conn)
        version_before = conn.execute("PRAGMA user_version").fetchone()[0]

        # Now add a broken migration to the list
        def broken_migration(c: sqlite3.Connection) -> None:
            raise RuntimeError("intentional failure")

        original_migrations = MIGRATIONS.copy()
        MIGRATIONS.append(broken_migration)

        try:
            with pytest.raises(MigrationError):
                apply_migrations(conn)

            # Version should be unchanged
            version_after = conn.execute("PRAGMA user_version").fetchone()[0]
            assert version_after == version_before
        finally:
            # Restore original migrations
            MIGRATIONS.clear()
            MIGRATIONS.extend(original_migrations)

        conn.close()


class TestV0ToV1Schema:
    """Tests for the v0→v1 migration schema details."""

    def test_contact_singleton_constraint(self) -> None:
        from persona.migrations import apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)

        conn.execute("INSERT INTO contact (id, name) VALUES (1, 'Test')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO contact (id, name) VALUES (2, 'Second')")
        conn.close()

    def test_summary_singleton_constraint(self) -> None:
        from persona.migrations import apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)

        conn.execute("INSERT INTO summary (id, text) VALUES (1, 'Test')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO summary (id, text) VALUES (2, 'Second')")
        conn.close()

    def test_skill_unique_name_constraint(self) -> None:
        from persona.migrations import apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)

        conn.execute(
            "INSERT INTO skill (name, category) VALUES ('Python', 'Languages')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO skill (name, category) VALUES ('Python', 'Other')"
            )
        conn.close()

    def test_experience_has_position_column(self) -> None:
        from persona.migrations import apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)

        conn.execute(
            "INSERT INTO experience (title, company, position) VALUES ('Dev', 'Co', 0)"
        )
        row = conn.execute("SELECT position FROM experience").fetchone()
        assert row[0] == 0
        conn.close()


class TestMultiStepMigration:
    """Tests for multi-step migration scenarios (US4)."""

    def test_mock_v1_to_v2_migration_preserves_data(self) -> None:
        """Simulate a v1→v2 migration and verify data is preserved."""
        from persona.migrations import MIGRATIONS, apply_migrations

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Apply v0→v1 to get a working database
        apply_migrations(conn)

        # Insert test data at v1
        conn.execute(
            "INSERT INTO contact (id, name, email) "
            "VALUES (1, 'Test User', 'test@test.com')"
        )
        conn.execute("INSERT INTO summary (id, text) VALUES (1, 'My summary')")
        conn.execute(
            "INSERT INTO experience (title, company, position) VALUES ('Dev', 'Co', 0)"
        )
        conn.commit()

        # Define a test-only v1→v2 migration (adds a column)
        def mock_v1_to_v2(c: sqlite3.Connection) -> None:
            c.execute("ALTER TABLE contact ADD COLUMN twitter TEXT")

        original_migrations = MIGRATIONS.copy()
        MIGRATIONS.append(mock_v1_to_v2)

        try:
            apply_migrations(conn)

            # Verify version incremented
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            assert version == 2

            # Verify existing data is preserved
            contact = conn.execute("SELECT * FROM contact WHERE id = 1").fetchone()
            assert contact["name"] == "Test User"
            assert contact["email"] == "test@test.com"

            summary = conn.execute("SELECT text FROM summary WHERE id = 1").fetchone()
            assert summary["text"] == "My summary"

            exp = conn.execute("SELECT * FROM experience").fetchone()
            assert exp["title"] == "Dev"
        finally:
            MIGRATIONS.clear()
            MIGRATIONS.extend(original_migrations)

        conn.close()

    def test_version_incremented_correctly_across_multiple_migrations(self) -> None:
        """Apply multiple migrations sequentially and verify version tracking."""
        from persona.migrations import MIGRATIONS, apply_migrations

        conn = sqlite3.connect(":memory:")

        # Apply base migration
        apply_migrations(conn)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1

        # Add two more mock migrations
        def mock_v1_to_v2(c: sqlite3.Connection) -> None:
            c.execute("ALTER TABLE contact ADD COLUMN twitter TEXT")

        def mock_v2_to_v3(c: sqlite3.Connection) -> None:
            c.execute("ALTER TABLE contact ADD COLUMN bluesky TEXT")

        original_migrations = MIGRATIONS.copy()
        MIGRATIONS.append(mock_v1_to_v2)
        MIGRATIONS.append(mock_v2_to_v3)

        try:
            apply_migrations(conn)
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
        finally:
            MIGRATIONS.clear()
            MIGRATIONS.extend(original_migrations)

        conn.close()
