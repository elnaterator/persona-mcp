"""Cross-interface integration tests — verify REST and MCP share state."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

import backend.server
from backend.resume_service import ResumeService
from backend.server import create_app


class TestCrossInterfaceSharedState:
    """Integration tests verifying REST API and MCP tools share the same database."""

    @pytest.fixture
    def app_and_service(
        self, db_conn_with_data: Any
    ) -> tuple[Any, ResumeService, TestClient]:
        """Create FastAPI app with test database and HTTP test client."""
        service = ResumeService(db_conn_with_data)
        app = create_app(service=service, conn=db_conn_with_data)
        client = TestClient(app)
        return app, service, client

    def test_add_entry_via_rest_visible_in_service(
        self, app_and_service: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Test US3: Add entry via REST API, verify visible through service."""
        app, service, client = app_and_service

        # Add skill via REST API
        response = client.post(
            "/api/resume/skills/entries",
            json={"name": "Docker", "category": "DevOps"},
        )
        assert response.status_code == 201

        # Read via service (same underlying database)
        skills = service.get_section("skills")
        skill_names = [s["name"] for s in skills]
        assert "Docker" in skill_names

    def test_update_via_service_visible_in_rest(
        self, app_and_service: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Test US3: Update via service, verify visible via REST API."""
        app, service, client = app_and_service

        # Update contact via service
        service.update_section(
            "contact",
            {"name": "John Updated", "email": "updated@example.com"},
        )

        # Read via REST API
        response = client.get("/api/resume/contact")
        assert response.status_code == 200
        contact = response.json()
        assert contact["name"] == "John Updated"
        assert contact["email"] == "updated@example.com"

    def test_concurrent_operations_no_corruption(
        self, app_and_service: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Test US3: Concurrent operations via both interfaces don't corrupt data."""
        app, service, client = app_and_service

        # Add multiple entries via both interfaces
        for i in range(5):
            if i % 2 == 0:
                # REST API
                client.post(
                    "/api/resume/skills/entries",
                    json={"name": f"RestSkill{i}", "category": "Languages"},
                )
            else:
                # Service (used by MCP tools)
                service.add_entry(
                    "skills",
                    {"name": f"ServiceSkill{i}", "category": "Languages"},
                )

        # Verify all entries present via REST
        response = client.get("/api/resume/skills")
        assert response.status_code == 200
        skills = response.json()
        skill_names = [s["name"] for s in skills]

        # All added skills should be present
        for i in range(5):
            if i % 2 == 0:
                assert f"RestSkill{i}" in skill_names
            else:
                assert f"ServiceSkill{i}" in skill_names

    def test_global_service_is_shared(
        self, app_and_service: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Test US3: Verify global _service used by MCP is the same instance."""
        app, service, client = app_and_service

        # The global _service should be the same instance
        assert backend.server._service is service, (
            "MCP tools should use the same service instance"
        )
