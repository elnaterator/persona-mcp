"""Unit tests for persona.migrations module."""

import json
import sqlite3

import pytest


class TestApplyMigrations:
    """Tests for the migration framework."""

    def test_applies_all_migrations(self) -> None:
        from persona.migrations import SCHEMA_VERSION, apply_migrations

        conn = sqlite3.connect(":memory:")
        apply_migrations(conn)

        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == SCHEMA_VERSION
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

    def _apply_v0_to_v1(self) -> sqlite3.Connection:
        from persona.migrations import migrate_v0_to_v1

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        migrate_v0_to_v1(conn)
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        return conn

    def test_creates_contact_table(self) -> None:
        conn = self._apply_v0_to_v1()
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "contact" in tables
        conn.close()

    def test_creates_all_v1_tables(self) -> None:
        conn = self._apply_v0_to_v1()
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

    def test_contact_singleton_constraint(self) -> None:
        conn = self._apply_v0_to_v1()
        conn.execute("INSERT INTO contact (id, name) VALUES (1, 'Test')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO contact (id, name) VALUES (2, 'Second')")
        conn.close()

    def test_summary_singleton_constraint(self) -> None:
        conn = self._apply_v0_to_v1()
        conn.execute("INSERT INTO summary (id, text) VALUES (1, 'Test')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO summary (id, text) VALUES (2, 'Second')")
        conn.close()

    def test_skill_unique_name_constraint(self) -> None:
        conn = self._apply_v0_to_v1()
        conn.execute(
            "INSERT INTO skill (name, category) VALUES ('Python', 'Languages')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO skill (name, category) VALUES ('Python', 'Other')"
            )
        conn.close()

    def test_experience_has_position_column(self) -> None:
        conn = self._apply_v0_to_v1()
        conn.execute(
            "INSERT INTO experience (title, company, position) VALUES ('Dev', 'Co', 0)"
        )
        row = conn.execute("SELECT position FROM experience").fetchone()
        assert row[0] == 0
        conn.close()


class TestV1ToV2Migration:
    """Tests for the v1→v2 migration."""

    def _build_v1_db(self) -> sqlite3.Connection:
        """Return a v1 database with the old singleton tables."""
        from persona.migrations import migrate_v0_to_v1

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        migrate_v0_to_v1(conn)
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        return conn

    def test_v1_to_v2_creates_resume_version_table(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        migrate_v1_to_v2(conn)
        conn.commit()

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "resume_version" in tables
        conn.close()

    def test_v1_to_v2_creates_application_table(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        migrate_v1_to_v2(conn)
        conn.commit()

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "application" in tables
        conn.close()

    def test_v1_to_v2_migrates_existing_contact_data(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        conn.execute(
            "INSERT INTO contact (id, name, email, phone) "
            "VALUES (1, 'Jane Doe', 'jane@example.com', '+1-555-0100')"
        )
        conn.execute("INSERT INTO summary (id, text) VALUES (1, 'Great engineer.')")
        conn.commit()

        migrate_v1_to_v2(conn)
        conn.commit()

        row = conn.execute(
            "SELECT resume_data FROM resume_version WHERE is_default = 1"
        ).fetchone()
        assert row is not None
        data = json.loads(row["resume_data"])
        assert data["contact"]["name"] == "Jane Doe"
        assert data["contact"]["email"] == "jane@example.com"
        assert data["summary"] == "Great engineer."
        conn.close()

    def test_v1_to_v2_migrates_experience_data(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        conn.execute(
            "INSERT INTO experience (title, company, start_date, end_date, "
            "location, highlights, position) "
            "VALUES ('Engineer', 'Acme', '2020-01', '2023-01', 'NY', '[]', 0)"
        )
        conn.commit()

        migrate_v1_to_v2(conn)
        conn.commit()

        row = conn.execute(
            "SELECT resume_data FROM resume_version WHERE is_default = 1"
        ).fetchone()
        data = json.loads(row["resume_data"])
        assert len(data["experience"]) == 1
        assert data["experience"][0]["title"] == "Engineer"
        assert data["experience"][0]["company"] == "Acme"
        conn.close()

    def test_v1_to_v2_migrates_education_data(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        conn.execute(
            "INSERT INTO education (institution, degree, field, start_date, "
            "end_date, honors, position) "
            "VALUES ('MIT', 'B.S.', 'CS', '2015-09', '2019-05', 'Honors', 0)"
        )
        conn.commit()

        migrate_v1_to_v2(conn)
        conn.commit()

        row = conn.execute(
            "SELECT resume_data FROM resume_version WHERE is_default = 1"
        ).fetchone()
        data = json.loads(row["resume_data"])
        assert len(data["education"]) == 1
        assert data["education"][0]["institution"] == "MIT"
        assert data["education"][0]["degree"] == "B.S."
        conn.close()

    def test_v1_to_v2_migrates_skills_data(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        conn.execute(
            "INSERT INTO skill (name, category) VALUES ('Python', 'Languages')"
        )
        conn.execute("INSERT INTO skill (name, category) VALUES ('Docker', 'Tools')")
        conn.commit()

        migrate_v1_to_v2(conn)
        conn.commit()

        row = conn.execute(
            "SELECT resume_data FROM resume_version WHERE is_default = 1"
        ).fetchone()
        data = json.loads(row["resume_data"])
        skill_names = [s["name"] for s in data["skills"]]
        assert "Python" in skill_names
        assert "Docker" in skill_names
        conn.close()

    def test_v1_to_v2_drops_old_tables(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        migrate_v1_to_v2(conn)
        conn.commit()

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "contact" not in tables
        assert "summary" not in tables
        assert "experience" not in tables
        assert "education" not in tables
        assert "skill" not in tables
        conn.close()

    def test_v1_to_v2_empty_db_creates_empty_default(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        # No data inserted — empty v1 tables
        migrate_v1_to_v2(conn)
        conn.commit()

        row = conn.execute(
            "SELECT resume_data, is_default FROM resume_version WHERE is_default = 1"
        ).fetchone()
        assert row is not None
        data = json.loads(row["resume_data"])
        assert data["contact"] == {}
        assert data["summary"] == ""
        assert data["experience"] == []
        assert data["education"] == []
        assert data["skills"] == []
        conn.close()

    def test_v1_to_v2_default_version_has_label(self) -> None:
        from persona.migrations import migrate_v1_to_v2

        conn = self._build_v1_db()
        migrate_v1_to_v2(conn)
        conn.commit()

        row = conn.execute(
            "SELECT label FROM resume_version WHERE is_default = 1"
        ).fetchone()
        assert row is not None
        assert row["label"]  # non-empty label
        conn.close()


class TestMultiStepMigration:
    """Tests for multi-step migration scenarios."""

    def test_version_incremented_correctly_across_multiple_migrations(
        self,
    ) -> None:
        """Apply multiple migrations sequentially and verify version tracking."""
        from persona.migrations import MIGRATIONS, apply_migrations

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Apply all real migrations
        apply_migrations(conn)
        real_version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert real_version >= 2

        # Add two more mock migrations on top
        def mock_next_step_a(c: sqlite3.Connection) -> None:
            c.execute("ALTER TABLE resume_version ADD COLUMN tags TEXT")

        def mock_next_step_b(c: sqlite3.Connection) -> None:
            c.execute(
                "ALTER TABLE resume_version ADD COLUMN archived INTEGER DEFAULT 0"
            )

        original_migrations = MIGRATIONS.copy()
        MIGRATIONS.append(mock_next_step_a)
        MIGRATIONS.append(mock_next_step_b)

        try:
            apply_migrations(conn)
            new_version = conn.execute("PRAGMA user_version").fetchone()[0]
            assert new_version == real_version + 2
        finally:
            MIGRATIONS.clear()
            MIGRATIONS.extend(original_migrations)

        conn.close()

    def test_mock_migration_preserves_resume_version_data(self) -> None:
        """Simulate an additional migration and verify resume data is preserved."""
        from persona.migrations import MIGRATIONS, apply_migrations

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Apply real migrations (gets us to v2 with a default empty resume_version)
        apply_migrations(conn)

        # Insert known data into resume_version
        conn.execute(
            "UPDATE resume_version SET resume_data = ? WHERE is_default = 1",
            (json.dumps({"summary": "preserved summary"}),),
        )
        conn.commit()

        # Define a test-only next migration (adds a column)
        def mock_add_column(c: sqlite3.Connection) -> None:
            c.execute("ALTER TABLE resume_version ADD COLUMN notes TEXT")

        original_migrations = MIGRATIONS.copy()
        MIGRATIONS.append(mock_add_column)

        try:
            apply_migrations(conn)

            # Verify version incremented
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            assert version == len(original_migrations) + 1

            # Verify resume data preserved
            row = conn.execute(
                "SELECT resume_data FROM resume_version WHERE is_default = 1"
            ).fetchone()
            data = json.loads(row["resume_data"])
            assert data["summary"] == "preserved summary"
        finally:
            MIGRATIONS.clear()
            MIGRATIONS.extend(original_migrations)

        conn.close()
