"""Integration tests for persona MCP server — end-to-end tool invocation."""

from typing import Any

from psycopg import Connection


class TestServerSchema:
    """Integration tests for database schema initialization."""

    def test_schema_at_current_version(self, db_conn: Connection[Any]) -> None:
        from persona.migrations import SCHEMA_VERSION

        row = db_conn.execute("SELECT version FROM schema_version").fetchone()
        assert row is not None
        assert row["version"] == SCHEMA_VERSION


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
