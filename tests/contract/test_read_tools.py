"""Contract tests for persona read tools (get_resume, get_resume_section)."""

import sqlite3

import pytest


class TestGetResume:
    """Contract tests for the get_resume MCP tool."""

    def test_returns_full_resume_from_populated_db(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume

        result = get_resume(conn=db_conn_with_data)

        assert result["contact"]["name"] == "Jane Doe"
        assert result["contact"]["email"] == "jane@example.com"
        assert "Experienced software engineer" in result["summary"]
        assert len(result["experience"]) == 2
        assert result["experience"][0]["title"] == "Senior Software Engineer"
        assert len(result["education"]) == 2
        assert len(result["skills"]) == 8

    def test_returns_empty_resume_on_empty_db(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume

        result = get_resume(conn=db_conn)

        assert result["contact"]["name"] is None
        assert result["summary"] == ""
        assert result["experience"] == []
        assert result["education"] == []
        assert result["skills"] == []


class TestGetResumeSection:
    """Contract tests for the get_resume_section MCP tool."""

    def test_returns_contact_info(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section

        result = get_resume_section(section="contact", conn=db_conn_with_data)

        assert result["name"] == "Jane Doe"
        assert result["email"] == "jane@example.com"
        assert result["phone"] == "+1-555-0100"

    def test_returns_summary(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section

        result = get_resume_section(section="summary", conn=db_conn_with_data)

        assert isinstance(result, str)
        assert "Experienced software engineer" in result

    def test_returns_experience_list(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section

        result = get_resume_section(section="experience", conn=db_conn_with_data)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Senior Software Engineer"
        assert result[0]["company"] == "Acme Corp"

    def test_returns_education_list(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section

        result = get_resume_section(section="education", conn=db_conn_with_data)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["institution"] == "Stanford University"

    def test_returns_skills_list(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section

        result = get_resume_section(section="skills", conn=db_conn_with_data)

        assert isinstance(result, list)
        assert len(result) == 8
        python_skills = [s for s in result if s["name"] == "Python"]
        assert len(python_skills) == 1

    def test_error_on_invalid_section(self, db_conn: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section

        with pytest.raises(ValueError, match="Invalid section"):
            get_resume_section(section="invalid", conn=db_conn)
