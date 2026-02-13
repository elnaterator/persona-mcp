"""Unit tests for backend.resume_service module."""

import sqlite3

import pytest


class TestResumeServiceGetResume:
    """Tests for ResumeService.get_resume."""

    def test_returns_empty_resume_on_empty_db(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)
        resume = service.get_resume()

        assert resume.contact.name is None
        assert resume.summary == ""
        assert resume.experience == []
        assert resume.education == []
        assert resume.skills == []

    def test_returns_populated_resume(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        resume = service.get_resume()

        assert resume.contact.name == "Jane Doe"
        assert "Experienced software engineer" in resume.summary
        assert len(resume.experience) == 2
        assert len(resume.education) == 2
        assert len(resume.skills) == 8


class TestResumeServiceGetSection:
    """Tests for ResumeService.get_section."""

    def test_get_contact_section(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.get_section("contact")

        assert result["name"] == "Jane Doe"
        assert result["email"] == "jane@example.com"

    def test_get_summary_section(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.get_section("summary")

        assert "Experienced software engineer" in result

    def test_get_experience_section(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.get_section("experience")

        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_skills_section(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.get_section("skills")

        assert isinstance(result, list)
        assert len(result) == 8

    def test_invalid_section_raises(self, db_conn: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)
        with pytest.raises(ValueError, match="Invalid section"):
            service.get_section("invalid")


class TestResumeServiceUpdateSection:
    """Tests for ResumeService.update_section (contact and summary)."""

    def test_update_contact(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.update_section("contact", {"email": "new@example.com"})

        assert "contact" in result.lower() or "updated" in result.lower()

        section = service.get_section("contact")
        assert section["email"] == "new@example.com"
        assert section["name"] == "Jane Doe"  # preserved

    def test_update_summary(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.update_section("summary", {"text": "New summary."})

        assert "summary" in result.lower() or "updated" in result.lower()

        section = service.get_section("summary")
        assert section == "New summary."

    def test_update_invalid_section_raises(self, db_conn: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)
        with pytest.raises(ValueError, match="Invalid section"):
            service.update_section("experience", {"title": "x"})


class TestResumeServiceAddEntry:
    """Tests for ResumeService.add_entry."""

    def test_add_experience(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.add_entry("experience", {"title": "CTO", "company": "NewCo"})

        assert isinstance(result, str)

        section = service.get_section("experience")
        assert len(section) == 3
        assert section[0]["title"] == "CTO"

    def test_add_skill(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        service.add_entry("skills", {"name": "Rust", "category": "Languages"})

        section = service.get_section("skills")
        rust = [s for s in section if s["name"] == "Rust"]
        assert len(rust) == 1

    def test_add_education(self, db_conn_with_data: sqlite3.Connection) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        service.add_entry("education", {"institution": "MIT", "degree": "Ph.D."})

        section = service.get_section("education")
        assert len(section) == 3
        assert section[0]["institution"] == "MIT"

    def test_add_entry_invalid_section_raises(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)
        with pytest.raises(ValueError, match="Invalid section"):
            service.add_entry("contact", {"name": "x"})


class TestResumeServiceUpdateEntry:
    """Tests for ResumeService.update_entry."""

    def test_update_experience_entry(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.update_entry("experience", 0, {"title": "Staff Engineer"})

        assert isinstance(result, str)

        section = service.get_section("experience")
        assert section[0]["title"] == "Staff Engineer"
        assert section[0]["company"] == "Acme Corp"  # preserved

    def test_update_entry_out_of_range(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        with pytest.raises(ValueError, match="out of range"):
            service.update_entry("experience", 99, {"title": "x"})

    def test_update_entry_invalid_section_raises(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)
        with pytest.raises(ValueError, match="Invalid section"):
            service.update_entry("contact", 0, {"name": "x"})


class TestResumeServiceRemoveEntry:
    """Tests for ResumeService.remove_entry."""

    def test_remove_experience_entry(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        result = service.remove_entry("experience", 0)

        assert isinstance(result, str)

        section = service.get_section("experience")
        assert len(section) == 1
        assert section[0]["title"] == "Software Engineer"

    def test_remove_entry_out_of_range(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)
        with pytest.raises(ValueError, match="out of range"):
            service.remove_entry("experience", 99)

    def test_remove_entry_invalid_section_raises(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)
        with pytest.raises(ValueError, match="Invalid section"):
            service.remove_entry("contact", 0)
