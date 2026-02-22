"""Integration tests for persona MCP server — end-to-end tool invocation."""

import json
import time
from typing import Any

from psycopg import Connection


class TestServerSchema:
    """Integration tests for database schema initialization."""

    def test_schema_at_current_version(self, db_conn: Connection[Any]) -> None:
        from persona.migrations import SCHEMA_VERSION

        row = db_conn.execute("SELECT version FROM schema_version").fetchone()
        assert row is not None
        assert row["version"] == SCHEMA_VERSION


class TestServerReadTools:
    """Integration tests for read tools via direct function calls."""

    def test_get_resume_returns_full_data(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(conn=db_conn_with_data)  # type: ignore[arg-type]

        assert result["contact"]["name"] == "Jane Doe"
        assert len(result["experience"]) == 2
        assert len(result["education"]) == 2
        assert len(result["skills"]) == 8
        assert "Experienced software engineer" in result["summary"]

    def test_get_resume_section_contact(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section

        contact = get_resume_section(section="contact", conn=db_conn_with_data)  # type: ignore[arg-type]

        assert contact["name"] == "Jane Doe"
        assert contact["email"] == "jane@example.com"

    def test_get_resume_section_experience(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section

        experience = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]

        assert len(experience) == 2
        assert experience[0]["title"] == "Senior Software Engineer"
        assert experience[0]["company"] == "Acme Corp"
        assert experience[0]["highlights"] == [
            "Led migration of monolithic application to microservices",
            "Reduced deployment time by 60%",
        ]

    def test_result_is_json_serializable(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(conn=db_conn_with_data)  # type: ignore[arg-type]

        # Must be JSON-serializable for MCP transport
        serialized = json.dumps(result)
        assert isinstance(serialized, str)

    def test_performance_under_2s_with_large_dataset(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        """SC-003: System starts and is usable within 2 seconds."""
        from persona.tools.read import get_resume

        # Update default resume with 50 experience entries
        large_experience = [
            {
                "title": f"Engineer {i}",
                "company": f"Company {i}",
                "start_date": f"20{i % 25:02d}-01",
                "end_date": f"20{(i % 25) + 1:02d}-01",
                "location": f"City {i}",
                "highlights": [f"Built feature {i}"],
            }
            for i in range(50)
        ]
        resume_data = {
            "contact": {},
            "summary": "",
            "experience": large_experience,
            "education": [],
            "skills": [],
        }
        db_conn_with_data.execute(
            "UPDATE resume_version SET resume_data = %s WHERE is_default = 1",
            (json.dumps(resume_data),),
        )

        start = time.monotonic()
        result = get_resume(conn=db_conn_with_data)  # type: ignore[arg-type]
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, f"get_resume took {elapsed:.2f}s, expected <2s"
        assert len(result["experience"]) == 50


class TestServerWriteTools:
    """Integration tests for write tools — add, read back, update, remove."""

    def test_add_read_update_remove_experience(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry, remove_entry, update_entry

        # Add
        add_entry(
            section="experience",
            data={
                "title": "VP Engineering",
                "company": "BigCo",
                "start_date": "2024-01",
            },
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )
        experience = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert len(experience) == 3
        assert experience[0]["title"] == "VP Engineering"

        # Update
        update_entry(
            section="experience",
            index=0,
            data={"title": "SVP Engineering"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )
        experience = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert experience[0]["title"] == "SVP Engineering"

        # Remove
        remove_entry(section="experience", index=0, conn=db_conn_with_data)  # type: ignore[arg-type]
        experience = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert len(experience) == 2

    def test_update_contact_and_summary(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_section

        # Update contact
        update_section(
            section="contact",
            data={"name": "Jane Smith", "email": "smith@new.com"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )
        contact = get_resume_section(section="contact", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert contact["name"] == "Jane Smith"
        assert contact["email"] == "smith@new.com"
        # Phone preserved
        assert contact["phone"] == "+1-555-0100"

        # Update summary
        update_section(
            section="summary",
            data={"text": "Updated summary."},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )
        summary = get_resume_section(section="summary", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert summary == "Updated summary."

    def test_write_results_are_json_serializable(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.write import add_entry

        result = add_entry(
            section="skills",
            data={"name": "NewLang", "category": "Languages"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )
        serialized = json.dumps(result)
        assert isinstance(serialized, str)


class TestMCPOverHTTP:
    """Integration tests for MCP accessible via streamable-http."""

    def test_mcp_app_mounted(self, db_conn_with_data: Connection[Any]) -> None:
        """MCP server is mounted at /mcp endpoint."""
        from persona.resume_service import ResumeService
        from persona.server import create_app

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        app = create_app(service=service, conn=db_conn_with_data)  # type: ignore[arg-type]

        routes = [getattr(route, "path", None) for route in app.routes]
        assert "/mcp" in routes, "MCP endpoint should be mounted at /mcp"

    def test_rest_and_mcp_share_service(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        """REST API and MCP tools use the same ResumeService instance."""
        import persona.server
        from persona.resume_service import ResumeService
        from persona.server import create_app

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        create_app(service=service, conn=db_conn_with_data)  # type: ignore[arg-type]

        assert persona.server._service is service, (
            "MCP tools should use the same service as REST API"
        )
