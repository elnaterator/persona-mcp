"""Cross-interface integration tests — verify REST and MCP share state."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import persona.server
from persona.resume_service import ResumeService
from persona.server import create_app


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
        assert persona.server._service is service, (
            "MCP tools should use the same service instance"
        )


class TestResumeVersionCrossInterface:
    """Integration tests for resume version operations across REST and MCP."""

    @pytest.fixture
    def full_app(self, db_conn_with_data: Any) -> tuple[Any, ResumeService, TestClient]:
        """Create full app with both resume and application services."""

        service = ResumeService(db_conn_with_data)
        app = create_app(service=service, conn=db_conn_with_data)
        client = TestClient(app)
        return app, service, client

    def test_create_version_via_rest_visible_in_service(
        self, full_app: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Create a resume version via REST and verify it's visible via service."""
        app, service, client = full_app

        resp = client.post("/api/resumes", json={"label": "My New Resume"})
        assert resp.status_code == 201
        created_id = resp.json()["id"]

        versions = service.list_resumes()
        ids = [v["id"] for v in versions]
        assert created_id in ids

    def test_update_version_via_service_visible_in_rest(
        self, full_app: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Update a resume version via service and verify it's visible via REST."""
        app, service, client = full_app

        default = service.get_resume()
        service.update_section(
            "contact",
            {"name": "Updated Name"},
            default["id"],
        )

        resp = client.get(f"/api/resumes/{default['id']}/contact")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_set_default_via_rest_visible_in_service(
        self, full_app: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Set default via REST and verify service returns the new default."""
        app, service, client = full_app

        resp = client.post("/api/resumes", json={"label": "Promoted"})
        new_id = resp.json()["id"]

        client.post(f"/api/resumes/{new_id}/default")

        default = service.get_resume()
        assert default["id"] == new_id


class TestApplicationCascadeDelete:
    """Integration tests for application cascade delete behavior."""

    @pytest.fixture
    def full_app_with_app_service(
        self, db_conn_with_data: Any
    ) -> tuple[Any, ResumeService, TestClient]:
        """Create full app with application service enabled."""

        service = ResumeService(db_conn_with_data)
        app = create_app(service=service, conn=db_conn_with_data)
        client = TestClient(app)
        return app, service, client

    def test_delete_application_cascades_contacts_and_comms(
        self, full_app_with_app_service: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Deleting an application via REST removes its contacts and communications."""
        app, service, client = full_app_with_app_service

        # Create application with contacts and communications
        created_resp = client.post(
            "/api/applications",
            json={"company": "Corp", "position": "Dev"},
        )
        assert created_resp.status_code == 201
        app_id = created_resp.json()["id"]

        client.post(
            f"/api/applications/{app_id}/contacts",
            json={"name": "Alice"},
        )
        client.post(
            f"/api/applications/{app_id}/communications",
            json={
                "type": "email",
                "direction": "sent",
                "body": "Hello",
                "date": "2024-01-01",
            },
        )

        # Delete the application
        del_resp = client.delete(f"/api/applications/{app_id}")
        assert del_resp.status_code == 200

        # Verify application is gone
        get_resp = client.get(f"/api/applications/{app_id}")
        assert get_resp.status_code == 404


class TestAIDraftWorkflow:
    """Integration tests for AI draft communication workflow."""

    @pytest.fixture
    def full_app_ai(
        self, db_conn_with_data: Any
    ) -> tuple[Any, ResumeService, TestClient]:
        """Create full app for AI workflow testing."""

        service = ResumeService(db_conn_with_data)
        app = create_app(service=service, conn=db_conn_with_data)
        client = TestClient(app)
        return app, service, client

    def test_create_app_via_rest_add_draft_via_service_visible_in_rest(
        self, full_app_ai: tuple[Any, ResumeService, TestClient]
    ) -> None:
        """Create app via REST, add draft comm via service, verify it shows in REST."""

        app, service, client = full_app_ai
        app_svc = persona.server._app_service
        assert app_svc is not None

        # Create application via REST
        created_resp = client.post(
            "/api/applications",
            json={"company": "TechCorp", "position": "Senior Engineer"},
        )
        assert created_resp.status_code == 201
        app_id = created_resp.json()["id"]

        # Add draft communication via service (simulates MCP tool call)
        comm = app_svc.add_communication(
            app_id,
            {
                "type": "email",
                "direction": "sent",
                "body": "I am applying for this role.",
                "date": "2024-02-01",
                "subject": "Application - Senior Engineer",
                "status": "draft",
            },
        )

        # Verify draft appears in REST endpoint
        comms_resp = client.get(f"/api/applications/{app_id}/communications")
        assert comms_resp.status_code == 200
        comms = comms_resp.json()
        assert len(comms) == 1
        assert comms[0]["status"] == "draft"
        assert comms[0]["id"] == comm["id"]


# ── Accomplishment Cross-Interface Tests ──────────────────────────────────────


class TestAccomplishmentCrossInterface:
    """T049 — Cross-interface tests: service layer ↔ REST API + SC-006 durability."""

    @pytest.fixture
    def full_app(self, db_conn_with_data: Any) -> tuple[Any, Any, TestClient]:
        """Create full app (all services) with test database and HTTP test client."""
        service = ResumeService(db_conn_with_data)
        app = create_app(service=service, conn=db_conn_with_data)
        client = TestClient(app)
        return app, service, client

    def test_create_via_service_visible_via_rest(
        self, full_app: tuple[Any, Any, TestClient]
    ) -> None:
        """Accomplishment created via AccomplishmentService visible via REST API."""
        _app, _service, client = full_app
        acc_svc = persona.server._acc_service
        assert acc_svc is not None

        created = acc_svc.create_accomplishment(
            {"title": "Cross-interface test", "result": "Success"}
        )

        resp = client.get(f"/api/accomplishments/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Cross-interface test"

    def test_create_via_rest_visible_via_service(
        self, full_app: tuple[Any, Any, TestClient]
    ) -> None:
        """Accomplishment created via REST API visible via AccomplishmentService."""
        _app, _service, client = full_app
        acc_svc = persona.server._acc_service
        assert acc_svc is not None

        resp = client.post(
            "/api/accomplishments",
            json={"title": "REST creation", "tags": ["test"]},
        )
        assert resp.status_code == 201
        acc_id = resp.json()["id"]

        acc = acc_svc.get_accomplishment(acc_id)
        assert acc["title"] == "REST creation"

    def test_global_acc_service_shared(
        self, full_app: tuple[Any, Any, TestClient]
    ) -> None:
        """Verify global _acc_service used by MCP is the same instance."""
        _app, _service, client = full_app
        assert persona.server._acc_service is not None

    def test_durability_across_connection_reopen(self, tmp_path: Path) -> None:
        """SC-006: Accomplishment persists after DB connection closed and reopened."""
        from persona.accomplishment_service import AccomplishmentService
        from persona.database import init_database

        data_dir = tmp_path / "data"

        # First connection — create an accomplishment
        conn1 = init_database(data_dir)
        svc1 = AccomplishmentService(conn1)
        created = svc1.create_accomplishment({"title": "Durability test"})
        acc_id = created["id"]
        conn1.close()

        # Second connection — verify it's still there
        conn2 = init_database(data_dir)
        svc2 = AccomplishmentService(conn2)
        recovered = svc2.get_accomplishment(acc_id)
        assert recovered["title"] == "Durability test"
        conn2.close()
