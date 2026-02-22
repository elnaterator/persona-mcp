"""Contract tests for persona read tools (get_resume, get_resume_section)."""

from typing import Any

import pytest
from psycopg import Connection


class TestGetResume:
    """Contract tests for the get_resume MCP tool."""

    def test_returns_full_resume_from_populated_db(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(conn=db_conn_with_data)  # type: ignore[arg-type]

        assert result["contact"]["name"] == "Jane Doe"
        assert result["contact"]["email"] == "jane@example.com"
        assert "Experienced software engineer" in result["summary"]
        assert len(result["experience"]) == 2
        assert result["experience"][0]["title"] == "Senior Software Engineer"
        assert len(result["education"]) == 2
        assert len(result["skills"]) == 8

    def test_returns_empty_resume_on_empty_db(self, db_conn: Connection[Any]) -> None:
        from persona.tools.read import get_resume

        result = get_resume(conn=db_conn)  # type: ignore[arg-type]

        assert result["contact"]["name"] is None
        assert result["summary"] == ""
        assert result["experience"] == []
        assert result["education"] == []
        assert result["skills"] == []


class TestGetResumeSection:
    """Contract tests for the get_resume_section MCP tool."""

    def test_returns_contact_info(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="contact", conn=db_conn_with_data)  # type: ignore[arg-type]

        assert result["name"] == "Jane Doe"
        assert result["email"] == "jane@example.com"
        assert result["phone"] == "+1-555-0100"

    def test_returns_summary(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="summary", conn=db_conn_with_data)  # type: ignore[arg-type]

        assert isinstance(result, str)
        assert "Experienced software engineer" in result

    def test_returns_experience_list(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Senior Software Engineer"
        assert result[0]["company"] == "Acme Corp"

    def test_returns_education_list(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="education", conn=db_conn_with_data)  # type: ignore[arg-type]

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["institution"] == "Stanford University"

    def test_returns_skills_list(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]

        assert isinstance(result, list)
        assert len(result) == 8
        python_skills = [s for s in result if s["name"] == "Python"]
        assert len(python_skills) == 1

    def test_error_on_invalid_section(self, db_conn: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section

        with pytest.raises(ValueError, match="Invalid section"):
            get_resume_section(section="invalid", conn=db_conn)  # type: ignore[arg-type]


class TestResumeVersionReadTools:
    """Contract tests for resume version MCP read tools."""

    def test_list_resumes_returns_list(self, db_conn: Connection[Any]) -> None:
        from fastmcp import FastMCP

        from persona.resume_service import ResumeService
        from persona.tools.resume_tools import register_resume_tools

        mcp = FastMCP("test")
        service = ResumeService(db_conn)  # type: ignore[arg-type]
        register_resume_tools(mcp, lambda: service)

        result = service.list_resumes()
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_resume_default(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        version = service.get_resume()

        assert version["is_default"] is True
        assert version["resume_data"]["contact"]["name"] == "Jane Doe"

    def test_get_resume_by_id(self, db_conn: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)  # type: ignore[arg-type]
        second = service.create_resume("Second")
        version = service.get_resume(second["id"])

        assert version["id"] == second["id"]
        assert version["label"] == "Second"

    def test_get_resume_section_contact(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.models import Resume
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        version = service.get_resume()
        resume = Resume(**version["resume_data"])
        section = resume.model_dump()["contact"]

        assert section["name"] == "Jane Doe"

    def test_get_resume_section_experience(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.models import Resume
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        version = service.get_resume()
        resume = Resume(**version["resume_data"])
        section = resume.model_dump()["experience"]

        assert isinstance(section, list)
        assert len(section) == 2


class TestApplicationContextTool:
    """Contract tests for get_application_context MCP tool."""

    def test_returns_composite_context(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        svc.add_contact(app["id"], {"name": "Alice"})
        svc.add_communication(
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Hello",
                "date": "2024-01-01",
            },
        )
        context = svc.get_application_context(app["id"])

        assert context["application"]["id"] == app["id"]
        assert len(context["contacts"]) == 1
        assert len(context["communications"]) == 1

    def test_default_resume_populated(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        context = svc.get_application_context(app["id"])

        assert context["default_resume"] is not None

    def test_resume_version_none_when_not_linked(
        self, db_conn: Connection[Any]
    ) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        context = svc.get_application_context(app["id"])

        assert context["resume_version"] is None

    def test_raises_for_nonexistent_app(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="not found"):
            svc.get_application_context(9999)
