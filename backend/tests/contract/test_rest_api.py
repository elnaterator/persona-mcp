"""Contract tests for REST API endpoints per openapi.yaml."""

import sqlite3
from collections.abc import Generator

import pytest
from starlette.testclient import TestClient

from persona.api.routes import create_router
from persona.application_service import ApplicationService
from persona.resume_service import ResumeService
from tests.conftest import populate_sample_data


@pytest.fixture
def _rest_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory DB that allows cross-thread use (needed by Starlette TestClient)."""
    from persona.migrations import apply_migrations

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    apply_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture
def service(_rest_db: sqlite3.Connection) -> ResumeService:
    """ResumeService backed by an empty in-memory database."""
    return ResumeService(_rest_db)


@pytest.fixture
def service_with_data(_rest_db: sqlite3.Connection) -> ResumeService:
    """ResumeService backed by a pre-populated database."""
    populate_sample_data(_rest_db)
    return ResumeService(_rest_db)


@pytest.fixture
def app_service(_rest_db: sqlite3.Connection) -> ApplicationService:
    """ApplicationService backed by an empty in-memory database."""
    return ApplicationService(_rest_db)


def _make_client(svc: ResumeService) -> TestClient:
    """Create a TestClient from a ResumeService using the API router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(create_router(svc))
    return TestClient(app)


def _make_full_client(svc: ResumeService, app_svc: ApplicationService) -> TestClient:
    """Create a TestClient with both ResumeService and ApplicationService."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(create_router(svc, app_service=app_svc))
    return TestClient(app)


# --- T012: GET /health, GET /api/resume, GET /api/resume/{section} ---


class TestHealthEndpoint:
    def test_health_returns_ok(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestGetResume:
    def test_get_empty_resume(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.get("/api/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert "contact" in data
        assert "summary" in data
        assert "experience" in data
        assert "education" in data
        assert "skills" in data

    def test_get_populated_resume(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.get("/api/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert data["contact"]["name"] == "Jane Doe"
        assert data["summary"] != ""
        assert len(data["experience"]) == 2
        assert len(data["education"]) == 2
        assert len(data["skills"]) == 8


class TestGetSection:
    def test_get_contact_section(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.get("/api/resume/contact")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Jane Doe"

    def test_get_summary_section(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.get("/api/resume/summary")
        assert resp.status_code == 200
        assert "software engineer" in resp.json().lower()

    def test_get_experience_section(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.get("/api/resume/experience")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_education_section(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.get("/api/resume/education")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_skills_section(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.get("/api/resume/skills")
        assert resp.status_code == 200
        assert len(resp.json()) == 8


# --- T013: PUT /api/resume/contact, PUT /api/resume/summary ---


class TestUpdateContact:
    def test_update_contact_partial(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.put(
            "/api/resume/contact",
            json={"name": "John Doe", "email": "john@example.com"},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

        # Verify the data was saved
        get_resp = client.get("/api/resume/contact")
        assert get_resp.json()["name"] == "John Doe"
        assert get_resp.json()["email"] == "john@example.com"

    def test_update_contact_merge(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        # Update only email, other fields should be preserved
        resp = client.put(
            "/api/resume/contact",
            json={"email": "newemail@example.com"},
        )
        assert resp.status_code == 200

        get_resp = client.get("/api/resume/contact")
        assert get_resp.json()["email"] == "newemail@example.com"
        assert get_resp.json()["name"] == "Jane Doe"  # preserved


class TestUpdateSummary:
    def test_update_summary(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.put(
            "/api/resume/summary",
            json={"text": "A new summary text."},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

        get_resp = client.get("/api/resume/summary")
        assert get_resp.json() == "A new summary text."

    def test_update_summary_empty_text_returns_422(
        self, service: ResumeService
    ) -> None:
        client = _make_client(service)
        resp = client.put("/api/resume/summary", json={"text": ""})
        assert resp.status_code == 422
        assert "detail" in resp.json()


# --- T014: POST entries, PUT entries/{index}, DELETE entries/{index} ---


class TestAddEntry:
    def test_add_experience_entry(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.post(
            "/api/resume/experience/entries",
            json={"title": "Engineer", "company": "TestCo"},
        )
        assert resp.status_code == 201
        assert "message" in resp.json()

        # Verify it was added
        get_resp = client.get("/api/resume/experience")
        assert len(get_resp.json()) == 1
        assert get_resp.json()[0]["title"] == "Engineer"

    def test_add_education_entry(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.post(
            "/api/resume/education/entries",
            json={"institution": "MIT", "degree": "B.S."},
        )
        assert resp.status_code == 201
        assert "message" in resp.json()

    def test_add_skill_entry(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.post(
            "/api/resume/skills/entries",
            json={"name": "Python", "category": "Languages"},
        )
        assert resp.status_code == 201
        assert "message" in resp.json()


class TestUpdateEntry:
    def test_update_experience_entry(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.put(
            "/api/resume/experience/entries/0",
            json={"title": "Staff Engineer"},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

        get_resp = client.get("/api/resume/experience")
        assert get_resp.json()[0]["title"] == "Staff Engineer"

    def test_update_skill_entry(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.put(
            "/api/resume/skills/entries/0",
            json={"category": "Core Languages"},
        )
        assert resp.status_code == 200


class TestDeleteEntry:
    def test_delete_experience_entry(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.delete("/api/resume/experience/entries/0")
        assert resp.status_code == 200
        assert "message" in resp.json()

        get_resp = client.get("/api/resume/experience")
        assert len(get_resp.json()) == 1

    def test_delete_skill_entry(self, service_with_data: ResumeService) -> None:
        client = _make_client(service_with_data)
        resp = client.delete("/api/resume/skills/entries/0")
        assert resp.status_code == 200

        get_resp = client.get("/api/resume/skills")
        assert len(get_resp.json()) == 7


# --- T015: Error cases ---


class TestErrorCases:
    def test_invalid_section_returns_404(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.get("/api/resume/invalid_section")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_add_entry_invalid_section_returns_400(
        self, service: ResumeService
    ) -> None:
        client = _make_client(service)
        resp = client.post(
            "/api/resume/contact/entries",
            json={"name": "test"},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_update_entry_out_of_range_returns_404(
        self, service: ResumeService
    ) -> None:
        client = _make_client(service)
        resp = client.put(
            "/api/resume/experience/entries/99",
            json={"title": "Ghost"},
        )
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_delete_entry_out_of_range_returns_404(
        self, service: ResumeService
    ) -> None:
        client = _make_client(service)
        resp = client.delete("/api/resume/experience/entries/99")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_add_experience_missing_required_fields_returns_422(
        self, service: ResumeService
    ) -> None:
        client = _make_client(service)
        resp = client.post(
            "/api/resume/experience/entries",
            json={"title": "Engineer"},  # missing 'company'
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_malformed_json_returns_422(self, service: ResumeService) -> None:
        client = _make_client(service)
        resp = client.put(
            "/api/resume/contact",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# --- Resume Version Endpoints ---


class TestResumeVersionEndpoints:
    def test_list_resumes(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.get("/api/resumes")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_create_resume(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.post("/api/resumes", json={"label": "My Custom Resume"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["label"] == "My Custom Resume"
        assert data["is_default"] is False

    def test_create_resume_missing_label_returns_422(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.post("/api/resumes", json={"label": ""})
        assert resp.status_code == 422

    def test_get_default_resume(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.get("/api/resumes/default")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_default"] is True
        assert "resume_data" in data

    def test_get_resume_by_id(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.get(f"/api/resumes/{version_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == version_id

    def test_get_resume_by_id_not_found(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.get("/api/resumes/9999")
        assert resp.status_code == 404

    def test_update_resume_metadata(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.put(f"/api/resumes/{version_id}", json={"label": "Renamed"})
        assert resp.status_code == 200
        assert resp.json()["label"] == "Renamed"

    def test_delete_resume_version(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        created = client.post("/api/resumes", json={"label": "Temp"}).json()
        resp = client.delete(f"/api/resumes/{created['id']}")
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_delete_last_version_returns_409(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        versions = client.get("/api/resumes").json()
        assert len(versions) == 1
        resp = client.delete(f"/api/resumes/{versions[0]['id']}")
        assert resp.status_code == 409

    def test_set_resume_default(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        created = client.post("/api/resumes", json={"label": "New Default"}).json()
        resp = client.put(f"/api/resumes/{created['id']}/default")
        assert resp.status_code == 200
        assert "message" in resp.json()

        default = client.get("/api/resumes/default").json()
        assert default["id"] == created["id"]

    def test_get_resume_section(
        self,
        service_with_data: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service_with_data, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.get(f"/api/resumes/{version_id}/contact")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Jane Doe"

    def test_get_resume_invalid_section_returns_404(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.get(f"/api/resumes/{version_id}/invalid_section")
        assert resp.status_code == 404

    def test_update_resume_contact(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.put(
            f"/api/resumes/{version_id}/contact",
            json={"name": "Alice"},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_update_resume_summary(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.put(
            f"/api/resumes/{version_id}/summary",
            json={"text": "New summary"},
        )
        assert resp.status_code == 200

    def test_add_resume_entry(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.post(
            f"/api/resumes/{version_id}/experience/entries",
            json={"title": "Dev", "company": "Corp"},
        )
        assert resp.status_code == 201
        assert "message" in resp.json()

    def test_update_resume_entry(
        self,
        service_with_data: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service_with_data, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.put(
            f"/api/resumes/{version_id}/experience/entries/0",
            json={"title": "Staff Engineer"},
        )
        assert resp.status_code == 200

    def test_delete_resume_entry(
        self,
        service_with_data: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service_with_data, app_service)
        versions = client.get("/api/resumes").json()
        version_id = versions[0]["id"]
        resp = client.delete(f"/api/resumes/{version_id}/experience/entries/0")
        assert resp.status_code == 200


# --- Application Endpoints ---


class TestApplicationEndpoints:
    def test_list_applications_empty(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.get("/api/applications")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_application(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Engineer"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["company"] == "Acme"
        assert data["position"] == "Engineer"
        assert data["id"] is not None

    def test_create_application_missing_company_returns_422(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.post("/api/applications", json={"position": "Dev"})
        assert resp.status_code == 422

    def test_create_application_invalid_status_returns_422(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.post(
            "/api/applications",
            json={"company": "Corp", "position": "Dev", "status": "Bogus"},
        )
        assert resp.status_code == 422

    def test_get_application(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        created = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.get(f"/api/applications/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_application_not_found(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.get("/api/applications/9999")
        assert resp.status_code == 404

    def test_update_application(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        created = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.put(
            f"/api/applications/{created['id']}",
            json={"status": "Applied"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Applied"

    def test_update_application_invalid_status_returns_422(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        created = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.put(
            f"/api/applications/{created['id']}",
            json={"status": "Nope"},
        )
        assert resp.status_code == 422

    def test_delete_application(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        created = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.delete(f"/api/applications/{created['id']}")
        assert resp.status_code == 200
        assert "message" in resp.json()

        get_resp = client.get(f"/api/applications/{created['id']}")
        assert get_resp.status_code == 404

    def test_delete_application_not_found(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.delete("/api/applications/9999")
        assert resp.status_code == 404

    def test_list_applications_filter_by_status(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        client.post(
            "/api/applications",
            json={"company": "A", "position": "P1", "status": "Applied"},
        )
        client.post(
            "/api/applications",
            json={"company": "B", "position": "P2", "status": "Interested"},
        )
        resp = client.get("/api/applications?status=Applied")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["company"] == "A"


# --- Contact Endpoints ---


class TestContactEndpoints:
    def test_list_contacts_empty(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.get(f"/api/applications/{app['id']}/contacts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_contact(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.post(
            f"/api/applications/{app['id']}/contacts",
            json={"name": "Alice", "email": "alice@corp.com"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Alice"
        assert data["email"] == "alice@corp.com"

    def test_add_contact_missing_name_returns_422(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.post(
            f"/api/applications/{app['id']}/contacts",
            json={"role": "HR"},
        )
        assert resp.status_code == 422

    def test_add_contact_app_not_found(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.post(
            "/api/applications/9999/contacts",
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404

    def test_update_contact(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        contact = client.post(
            f"/api/applications/{app['id']}/contacts",
            json={"name": "Alice"},
        ).json()
        resp = client.put(
            f"/api/applications/{app['id']}/contacts/{contact['id']}",
            json={"role": "Engineering Manager"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "Engineering Manager"

    def test_delete_contact(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        contact = client.post(
            f"/api/applications/{app['id']}/contacts",
            json={"name": "Alice"},
        ).json()
        resp = client.delete(f"/api/applications/{app['id']}/contacts/{contact['id']}")
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_delete_contact_not_found(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.delete(f"/api/applications/{app['id']}/contacts/9999")
        assert resp.status_code == 404


# --- Communication Endpoints ---


class TestCommunicationEndpoints:
    def test_list_communications_empty(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.get(f"/api/applications/{app['id']}/communications")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_communication(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.post(
            f"/api/applications/{app['id']}/communications",
            json={
                "type": "email",
                "direction": "sent",
                "body": "Applying for the role.",
                "date": "2024-01-01",
                "subject": "Application",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "email"
        assert data["subject"] == "Application"

    def test_add_communication_missing_body_returns_422(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.post(
            f"/api/applications/{app['id']}/communications",
            json={"type": "email", "direction": "sent", "date": "2024-01-01"},
        )
        assert resp.status_code == 422

    def test_add_communication_app_not_found(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.post(
            "/api/applications/9999/communications",
            json={
                "type": "email",
                "direction": "sent",
                "body": "Hi",
                "date": "2024-01-01",
            },
        )
        assert resp.status_code == 404

    def test_update_communication(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        comm = client.post(
            f"/api/applications/{app['id']}/communications",
            json={
                "type": "email",
                "direction": "sent",
                "body": "Draft.",
                "date": "2024-01-01",
            },
        ).json()
        resp = client.put(
            f"/api/applications/{app['id']}/communications/{comm['id']}",
            json={"status": "draft"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    def test_delete_communication(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        comm = client.post(
            f"/api/applications/{app['id']}/communications",
            json={
                "type": "email",
                "direction": "sent",
                "body": "Hello",
                "date": "2024-01-01",
                "subject": "Greetings",
            },
        ).json()
        resp = client.delete(
            f"/api/applications/{app['id']}/communications/{comm['id']}"
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_delete_communication_not_found(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.delete(f"/api/applications/{app['id']}/communications/9999")
        assert resp.status_code == 404


# --- Application Context Endpoint ---


class TestApplicationContextEndpoint:
    def test_get_context_returns_composite(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Dev"},
        ).json()
        resp = client.get(f"/api/applications/{app['id']}/context")
        assert resp.status_code == 200
        data = resp.json()
        assert "application" in data
        assert "contacts" in data
        assert "communications" in data
        assert "default_resume" in data

    def test_context_application_data_matches(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        app = client.post(
            "/api/applications",
            json={"company": "Acme", "position": "Engineer"},
        ).json()
        resp = client.get(f"/api/applications/{app['id']}/context")
        assert resp.status_code == 200
        data = resp.json()
        assert data["application"]["company"] == "Acme"
        assert data["application"]["position"] == "Engineer"

    def test_context_not_found_returns_404(
        self,
        service: ResumeService,
        app_service: ApplicationService,
    ) -> None:
        client = _make_full_client(service, app_service)
        resp = client.get("/api/applications/9999/context")
        assert resp.status_code == 404
