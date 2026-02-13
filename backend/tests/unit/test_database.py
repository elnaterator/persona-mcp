"""Unit tests for persona.database module."""

import sqlite3
from pathlib import Path

import pytest


class TestInitDatabase:
    """Tests for init_database function."""

    def test_creates_db_file(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        assert (tmp_path / "persona.db").exists()
        conn.close()

    def test_creates_data_dir_if_missing(self, tmp_path: Path) -> None:
        from persona.database import init_database

        data_dir = tmp_path / "nested" / "dir"
        conn = init_database(data_dir)
        assert (data_dir / "persona.db").exists()
        conn.close()

    def test_sets_wal_mode(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_sets_foreign_keys_on(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
        conn.close()

    def test_sets_busy_timeout(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert timeout == 5000
        conn.close()

    def test_runs_migrations(self, tmp_path: Path) -> None:
        from persona.database import init_database
        from persona.migrations import SCHEMA_VERSION

        conn = init_database(tmp_path)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == SCHEMA_VERSION
        conn.close()

    def test_returns_connection(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()


class TestLoadResume:
    """Tests for load_resume on empty and populated databases."""

    def test_load_resume_empty_db(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn)

        assert resume.contact.name is None
        assert resume.summary == ""
        assert resume.experience == []
        assert resume.education == []
        assert resume.skills == []

    def test_load_resume_with_data(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn_with_data)

        assert resume.contact.name == "Jane Doe"
        assert resume.contact.email == "jane@example.com"
        assert "Experienced software engineer" in resume.summary
        assert len(resume.experience) == 2
        assert resume.experience[0].title == "Senior Software Engineer"
        assert len(resume.education) == 2
        assert resume.education[0].institution == "Stanford University"
        assert len(resume.skills) == 8


class TestLoadSection:
    """Tests for load_section for each section type."""

    def test_load_contact_empty(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn)
        assert resume.contact.name is None

    def test_load_contact_with_data(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn_with_data)
        assert resume.contact.name == "Jane Doe"

    def test_load_summary_empty(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn)
        assert resume.summary == ""

    def test_load_summary_with_data(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn_with_data)
        assert "Experienced software engineer" in resume.summary

    def test_load_experience_empty(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn)
        assert resume.experience == []

    def test_load_experience_with_data(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn_with_data)
        assert len(resume.experience) == 2
        assert resume.experience[0].title == "Senior Software Engineer"

    def test_load_education_with_data(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn_with_data)
        assert len(resume.education) == 2
        assert resume.education[0].institution == "Stanford University"

    def test_load_skills_with_data(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.database import load_resume

        resume = load_resume(db_conn_with_data)
        assert len(resume.skills) == 8
        python_skills = [s for s in resume.skills if s.name == "Python"]
        assert len(python_skills) == 1

    def test_load_section_invalid(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_section

        with pytest.raises(ValueError, match="Invalid section"):
            load_section(db_conn, "invalid")

    def test_round_trip_fidelity(self, db_conn: sqlite3.Connection) -> None:
        """SC-001: Data written and read back must match exactly."""
        from persona.database import (
            load_resume,
            save_contact,
            save_summary,
        )

        save_contact(
            db_conn,
            {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+1-555-1234",
            },
        )
        save_summary(db_conn, "A test summary.")

        resume = load_resume(db_conn)
        assert resume.contact.name == "Test User"
        assert resume.contact.email == "test@example.com"
        assert resume.contact.phone == "+1-555-1234"
        assert resume.summary == "A test summary."


class TestSaveContact:
    """Tests for save_contact with partial merge semantics."""

    def test_save_contact_creates_row(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import save_contact

        save_contact(db_conn, {"name": "Jane", "email": "jane@test.com"})

        row = db_conn.execute("SELECT * FROM contact WHERE id = 1").fetchone()
        assert row["name"] == "Jane"
        assert row["email"] == "jane@test.com"
        assert row["phone"] is None

    def test_save_contact_partial_merge(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume, save_contact

        save_contact(db_conn_with_data, {"email": "new@example.com"})

        resume = load_resume(db_conn_with_data)
        assert resume.contact.email == "new@example.com"
        assert resume.contact.name == "Jane Doe"  # preserved

    def test_save_contact_empty_raises(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import save_contact

        with pytest.raises(ValueError, match="At least one contact field"):
            save_contact(db_conn, {})

    def test_save_contact_unknown_fields_ignored(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import save_contact

        with pytest.raises(ValueError, match="At least one contact field"):
            save_contact(db_conn, {"unknown_field": "value"})


class TestSaveSummary:
    """Tests for save_summary (full replace)."""

    def test_save_summary_creates_row(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import save_summary

        save_summary(db_conn, "My summary")

        row = db_conn.execute("SELECT text FROM summary WHERE id = 1").fetchone()
        assert row["text"] == "My summary"

    def test_save_summary_replaces(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.database import load_resume, save_summary

        save_summary(db_conn_with_data, "New summary")
        resume = load_resume(db_conn_with_data)
        assert resume.summary == "New summary"

    def test_save_summary_empty_raises(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import save_summary

        with pytest.raises(ValueError, match="Summary text must not be empty"):
            save_summary(db_conn, "")


class TestExperienceEntryManagement:
    """Tests for add/update/remove experience entries."""

    def test_add_experience_prepends_at_position_0(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import add_experience, load_resume

        add_experience(db_conn_with_data, {"title": "CTO", "company": "NewCo"})

        resume = load_resume(db_conn_with_data)
        assert len(resume.experience) == 3
        assert resume.experience[0].title == "CTO"
        assert resume.experience[1].title == "Senior Software Engineer"

    def test_update_experience_preserves_ordering(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume, update_experience

        update_experience(db_conn_with_data, 0, {"title": "Staff Engineer"})

        resume = load_resume(db_conn_with_data)
        assert resume.experience[0].title == "Staff Engineer"
        assert resume.experience[0].company == "Acme Corp"
        assert resume.experience[1].title == "Software Engineer"

    def test_remove_experience_compacts_positions(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume, remove_experience

        removed = remove_experience(db_conn_with_data, 0)
        assert removed.title == "Senior Software Engineer"

        resume = load_resume(db_conn_with_data)
        assert len(resume.experience) == 1
        assert resume.experience[0].title == "Software Engineer"

    def test_remove_experience_out_of_range(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import remove_experience

        with pytest.raises(ValueError, match="out of range"):
            remove_experience(db_conn_with_data, 99)

    def test_update_experience_out_of_range(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import update_experience

        with pytest.raises(ValueError, match="out of range"):
            update_experience(db_conn_with_data, 99, {"title": "x"})

    def test_add_experience_on_empty_db(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import add_experience, load_resume

        add_experience(db_conn, {"title": "Dev", "company": "Co"})

        resume = load_resume(db_conn)
        assert len(resume.experience) == 1
        assert resume.experience[0].title == "Dev"


class TestEducationEntryManagement:
    """Tests for add/update/remove education entries."""

    def test_add_education_prepends(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import add_education, load_resume

        add_education(
            db_conn_with_data,
            {"institution": "MIT", "degree": "Ph.D."},
        )

        resume = load_resume(db_conn_with_data)
        assert len(resume.education) == 3
        assert resume.education[0].institution == "MIT"

    def test_update_education_by_index(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume, update_education

        update_education(db_conn_with_data, 0, {"honors": "Magna Cum Laude"})

        resume = load_resume(db_conn_with_data)
        assert resume.education[0].honors == "Magna Cum Laude"
        assert resume.education[0].institution == "Stanford University"

    def test_remove_education_compacts(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_resume, remove_education

        removed = remove_education(db_conn_with_data, 0)
        assert removed.institution == "Stanford University"

        resume = load_resume(db_conn_with_data)
        assert len(resume.education) == 1
        assert resume.education[0].institution == "UC Berkeley"

    def test_education_index_out_of_range(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import remove_education

        with pytest.raises(ValueError, match="out of range"):
            remove_education(db_conn_with_data, 99)


class TestSkillEntryManagement:
    """Tests for add/update/remove skill entries."""

    def test_add_skill_with_default_category(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import add_skill, load_resume

        add_skill(db_conn, {"name": "Docker"})

        resume = load_resume(db_conn)
        assert len(resume.skills) == 1
        assert resume.skills[0].name == "Docker"
        assert resume.skills[0].category == "Other"

    def test_duplicate_skill_rejected_case_insensitive(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import add_skill

        with pytest.raises(ValueError, match="already exists"):
            add_skill(db_conn_with_data, {"name": "python"})

    def test_update_skill_by_index(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.database import load_resume, update_skill

        update_skill(db_conn_with_data, 0, {"name": "Python 3"})

        resume = load_resume(db_conn_with_data)
        assert resume.skills[0].name == "Python 3"

    def test_remove_skill_by_index(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.database import load_resume, remove_skill

        removed = remove_skill(db_conn_with_data, 0)
        assert removed.name == "Python"

        resume = load_resume(db_conn_with_data)
        assert len(resume.skills) == 7
        assert all(s.name != "Python" for s in resume.skills)

    def test_skill_index_out_of_range(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import remove_skill

        with pytest.raises(ValueError, match="out of range"):
            remove_skill(db_conn_with_data, 99)
