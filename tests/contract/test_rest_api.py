"""Contract tests for REST API endpoints per openapi.yaml."""

import sqlite3
from collections.abc import Generator

import pytest
from starlette.testclient import TestClient

from backend.api.routes import create_router
from backend.resume_service import ResumeService
from tests.conftest import populate_sample_data


@pytest.fixture
def _rest_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory DB that allows cross-thread use (needed by Starlette TestClient)."""
    from backend.migrations import apply_migrations

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


def _make_client(svc: ResumeService) -> TestClient:
    """Create a TestClient from a ResumeService using the API router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(create_router(svc))
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
