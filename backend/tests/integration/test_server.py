"""Integration tests for persona MCP server — end-to-end tool invocation via SQLite."""

import json
import sqlite3
import time
from pathlib import Path


class TestServerAutoInit:
    """Integration tests for database auto-initialization."""

    def test_auto_creates_data_dir_and_db(self, tmp_path: Path) -> None:
        from persona.database import init_database

        data_dir = tmp_path / "fresh" / "data"
        conn = init_database(data_dir)

        assert data_dir.exists()
        assert (data_dir / "persona.db").exists()
        conn.close()

    def test_schema_at_current_version_after_init(self, tmp_path: Path) -> None:
        from persona.database import init_database
        from persona.migrations import SCHEMA_VERSION

        conn = init_database(tmp_path)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == SCHEMA_VERSION
        conn.close()

    def test_transparent_schema_upgrade_on_restart(self, tmp_path: Path) -> None:
        """Simulates server restart with a pending migration."""
        from persona.migrations import MIGRATIONS, apply_migrations

        # First "startup" — create DB at current version
        db_path = tmp_path / "persona.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        apply_migrations(conn)

        # Insert data at current version
        conn.execute(
            "INSERT INTO resume_version (label, is_default, resume_data) "
            "VALUES ('Test Resume', 0, '{}')"
        )
        conn.commit()
        conn.close()

        # Add a mock next migration
        def mock_next_migration(c: sqlite3.Connection) -> None:
            c.execute("ALTER TABLE resume_version ADD COLUMN description TEXT")

        original = MIGRATIONS.copy()
        MIGRATIONS.append(mock_next_migration)

        try:
            # Second "startup" — should auto-apply the mock migration
            conn2 = sqlite3.connect(str(db_path))
            conn2.row_factory = sqlite3.Row
            apply_migrations(conn2)

            version = conn2.execute("PRAGMA user_version").fetchone()[0]
            assert version == len(MIGRATIONS)

            # Verify existing data preserved
            row = conn2.execute(
                "SELECT * FROM resume_version WHERE label = 'Test Resume'"
            ).fetchone()
            assert row is not None
            conn2.close()
        finally:
            MIGRATIONS.clear()
            MIGRATIONS.extend(original)

    def test_version_mismatch_raises(self, tmp_path: Path) -> None:
        """Server should refuse to start if DB version > code version."""
        import pytest

        from persona.database import init_database
        from persona.migrations import SchemaVersionError

        # Create DB and set future version
        conn = init_database(tmp_path)
        conn.execute("PRAGMA user_version = 999")
        conn.commit()
        conn.close()

        # Trying to init again should fail
        with pytest.raises(SchemaVersionError):
            init_database(tmp_path)


class TestServerReadTools:
    """Integration tests for read tools via direct function calls."""

    def test_get_resume_returns_full_data(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(conn=db_conn_with_data)

        assert result["contact"]["name"] == "Jane Doe"
        assert len(result["experience"]) == 2
        assert len(result["education"]) == 2
        assert len(result["skills"]) == 8
        assert "Experienced software engineer" in result["summary"]

    def test_get_resume_section_contact(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.tools.read import get_resume_section

        contact = get_resume_section(section="contact", conn=db_conn_with_data)

        assert contact["name"] == "Jane Doe"
        assert contact["email"] == "jane@example.com"

    def test_get_resume_section_experience(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.tools.read import get_resume_section

        experience = get_resume_section(section="experience", conn=db_conn_with_data)

        assert len(experience) == 2
        assert experience[0]["title"] == "Senior Software Engineer"
        assert experience[0]["company"] == "Acme Corp"
        assert experience[0]["highlights"] == [
            "Led migration of monolithic application to microservices",
            "Reduced deployment time by 60%",
        ]

    def test_result_is_json_serializable(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(conn=db_conn_with_data)

        # Must be JSON-serializable for MCP transport
        serialized = json.dumps(result)
        assert isinstance(serialized, str)

    def test_performance_under_2s_with_large_dataset(
        self, db_conn_with_data: sqlite3.Connection
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
            "UPDATE resume_version SET resume_data = ? WHERE is_default = 1",
            (json.dumps(resume_data),),
        )
        db_conn_with_data.commit()

        start = time.monotonic()
        result = get_resume(conn=db_conn_with_data)
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, f"get_resume took {elapsed:.2f}s, expected <2s"
        assert len(result["experience"]) == 50


class TestServerWriteTools:
    """Integration tests for write tools — add, read back, update, remove."""

    def test_add_read_update_remove_experience(
        self, db_conn_with_data: sqlite3.Connection
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
            conn=db_conn_with_data,
        )
        experience = get_resume_section(section="experience", conn=db_conn_with_data)
        assert len(experience) == 3
        assert experience[0]["title"] == "VP Engineering"

        # Update
        update_entry(
            section="experience",
            index=0,
            data={"title": "SVP Engineering"},
            conn=db_conn_with_data,
        )
        experience = get_resume_section(section="experience", conn=db_conn_with_data)
        assert experience[0]["title"] == "SVP Engineering"

        # Remove
        remove_entry(section="experience", index=0, conn=db_conn_with_data)
        experience = get_resume_section(section="experience", conn=db_conn_with_data)
        assert len(experience) == 2

    def test_update_contact_and_summary(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_section

        # Update contact
        update_section(
            section="contact",
            data={"name": "Jane Smith", "email": "smith@new.com"},
            conn=db_conn_with_data,
        )
        contact = get_resume_section(section="contact", conn=db_conn_with_data)
        assert contact["name"] == "Jane Smith"
        assert contact["email"] == "smith@new.com"
        # Phone preserved
        assert contact["phone"] == "+1-555-0100"

        # Update summary
        update_section(
            section="summary",
            data={"text": "Updated summary."},
            conn=db_conn_with_data,
        )
        summary = get_resume_section(section="summary", conn=db_conn_with_data)
        assert summary == "Updated summary."

    def test_write_results_are_json_serializable(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.tools.write import add_entry

        result = add_entry(
            section="skills",
            data={"name": "NewLang", "category": "Languages"},
            conn=db_conn_with_data,
        )
        serialized = json.dumps(result)
        assert isinstance(serialized, str)


class TestMCPOverHTTP:
    """Integration tests for MCP accessible via streamable-http."""

    def test_mcp_app_mounted(self, db_conn_with_data: sqlite3.Connection) -> None:
        """MCP server is mounted at /mcp endpoint."""
        from persona.resume_service import ResumeService
        from persona.server import create_app

        service = ResumeService(db_conn_with_data)
        app = create_app(service=service, conn=db_conn_with_data)

        routes = [getattr(route, "path", None) for route in app.routes]
        assert "/mcp" in routes, "MCP endpoint should be mounted at /mcp"

    def test_rest_and_mcp_share_service(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        """REST API and MCP tools use the same ResumeService instance."""
        import persona.server
        from persona.resume_service import ResumeService
        from persona.server import create_app

        service = ResumeService(db_conn_with_data)
        create_app(service=service, conn=db_conn_with_data)

        assert persona.server._service is service, (
            "MCP tools should use the same service as REST API"
        )
