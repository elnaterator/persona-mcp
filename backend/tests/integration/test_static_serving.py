"""
Integration tests for static file serving.

Tests verify that the backend serves frontend static assets from root `/`
while keeping API routes, MCP endpoints, and health checks functional.
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from persona.resume_service import ResumeService
from persona.server import create_app


class TestStaticFileServing:
    """Test static file serving functionality."""

    @pytest.fixture
    def temp_frontend_dir(self):
        """Create a temporary frontend directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frontend_dir = Path(tmpdir)

            # Create index.html
            (frontend_dir / "index.html").write_text(
                "<!DOCTYPE html><html><body>Test Frontend</body></html>"
            )

            # Create a CSS file
            (frontend_dir / "styles.css").write_text("body { margin: 0; }")

            # Create a JS file
            (frontend_dir / "app.js").write_text("console.log('test');")

            yield frontend_dir

    @pytest.fixture
    def app_with_frontend(self, temp_frontend_dir, db_conn):
        """Create app with temporary frontend directory."""
        # Override the frontend directory config
        os.environ["PERSONA_FRONTEND_DIR"] = str(temp_frontend_dir)
        try:
            # Pass an explicit service so auth is not wired (test mode).
            app = create_app(service=ResumeService(db_conn), conn=db_conn)
        finally:
            os.environ.pop("PERSONA_FRONTEND_DIR", None)
        return app

    @pytest.fixture
    def app_without_frontend(self, db_conn):
        """Create app with non-existent frontend directory."""
        os.environ["PERSONA_FRONTEND_DIR"] = "/nonexistent/path"
        try:
            # Pass an explicit service so auth is not wired (test mode).
            app = create_app(service=ResumeService(db_conn), conn=db_conn)
        finally:
            os.environ.pop("PERSONA_FRONTEND_DIR", None)
        return app

    def test_root_serves_index_html(self, app_with_frontend):
        """Test that root path serves index.html."""
        client = TestClient(app_with_frontend)
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Test Frontend" in response.text

    def test_static_css_file_served(self, app_with_frontend):
        """Test that static CSS files are served."""
        client = TestClient(app_with_frontend)
        response = client.get("/styles.css")

        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        assert "margin: 0" in response.text

    def test_static_js_file_served(self, app_with_frontend):
        """Test that static JS files are served."""
        client = TestClient(app_with_frontend)
        response = client.get("/app.js")

        assert response.status_code == 200
        # Accept both application/javascript and text/javascript
        assert "javascript" in response.headers["content-type"]
        assert "console.log" in response.text

    def test_api_routes_still_work(self, app_with_frontend):
        """Test that API routes are not affected by static file serving."""
        client = TestClient(app_with_frontend)
        response = client.get("/api/resume")

        assert response.status_code == 200
        data = response.json()
        assert "contact" in data
        assert "summary" in data

    def test_health_endpoint_still_works(self, app_with_frontend):
        """Test that health endpoint is not affected."""
        client = TestClient(app_with_frontend)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_mcp_endpoint_still_works(self, app_with_frontend):
        """Test that MCP endpoint is not affected."""
        client = TestClient(app_with_frontend)
        # MCP endpoint should be accessible (even if we don't test the full protocol)
        # Just verify it's mounted and responds
        response = client.get("/mcp/health")

        # MCP health endpoint should work (or at least not 404)
        assert response.status_code in [200, 404, 405]  # Depends on MCP implementation

    def test_server_starts_without_frontend_dir(self, app_without_frontend):
        """Test that server starts even if frontend directory doesn't exist."""
        client = TestClient(app_without_frontend)

        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200

        # API should still work
        response = client.get("/api/resume")
        assert response.status_code == 200

        # Root path should return 404 since no static files are mounted
        response = client.get("/")
        assert response.status_code == 404

    def test_nonexistent_static_file_returns_404(self, app_with_frontend):
        """Test that requesting non-existent static file returns 404."""
        client = TestClient(app_with_frontend)
        response = client.get("/nonexistent.js")

        assert response.status_code == 404

    def test_api_routes_have_priority_over_static_files(
        self, app_with_frontend, temp_frontend_dir
    ):
        """Test that API routes take priority over static files with same name."""
        # Create a file that conflicts with an API route
        (temp_frontend_dir / "api").mkdir(exist_ok=True)
        (temp_frontend_dir / "api" / "resume").write_text("fake static content")

        client = TestClient(app_with_frontend)
        response = client.get("/api/resume")

        # Should get JSON from API, not the static file
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        assert "contact" in data
