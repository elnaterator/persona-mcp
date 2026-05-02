"""Contract tests for contact REST API."""

from collections.abc import Generator
from typing import Any

import pytest
from psycopg import Connection
from starlette.testclient import TestClient

from persona.auth import current_user_id_var

_TEST_USER = "test_contact_user"


@pytest.fixture(autouse=True)
def _set_user_context() -> Generator[None, None, None]:
    token = current_user_id_var.set(_TEST_USER)
    try:
        yield
    finally:
        current_user_id_var.reset(token)


@pytest.fixture
def contact_service(db_conn: Connection[Any]) -> Any:
    from persona.contact_service import ContactService

    db_conn.execute(
        "INSERT INTO users (id, email) VALUES (%s, 'test@test.com') "
        "ON CONFLICT (id) DO NOTHING",
        (_TEST_USER,),
    )
    return ContactService(db_conn)  # type: ignore[arg-type]


def _make_contact_client(db_conn: Connection[Any]) -> TestClient:
    from fastapi import FastAPI

    from persona.api.routes import create_router
    from persona.contact_service import ContactService
    from persona.resume_service import ResumeService

    svc = ResumeService(db_conn)  # type: ignore[arg-type]
    contact_svc = ContactService(db_conn)  # type: ignore[arg-type]
    app = FastAPI()
    app.include_router(create_router(svc, contact_service=contact_svc))
    return TestClient(app)


# ── Create + Get ─────────────────────────────────────────────────────────────


class TestRESTCreateGetContact:
    def test_post_valid_returns_201(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        resp = client.post(
            "/api/contacts",
            json={"name": "Jane Doe", "company": "Acme", "tags": ["recruiter"]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Jane Doe"
        assert data["company"] == "Acme"
        assert "id" in data

    def test_post_missing_name_returns_422(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        resp = client.post("/api/contacts", json={"company": "Acme"})
        assert resp.status_code == 422

    def test_post_blank_name_returns_422(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        resp = client.post("/api/contacts", json={"name": "   "})
        assert resp.status_code == 422

    def test_get_by_id_returns_full_record(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        post_resp = client.post(
            "/api/contacts",
            json={"name": "Bob", "notes": "Very helpful", "email": "bob@example.com"},
        )
        contact_id = post_resp.json()["id"]
        get_resp = client.get(f"/api/contacts/{contact_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["notes"] == "Very helpful"
        assert data["email"] == "bob@example.com"

    def test_get_nonexistent_returns_404(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        resp = client.get("/api/contacts/99999")
        assert resp.status_code == 404


# ── List + Filter ─────────────────────────────────────────────────────────────


class TestRESTListContactsFilter:
    def test_list_returns_summaries(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        client.post("/api/contacts", json={"name": "Alice"})
        client.post("/api/contacts", json={"name": "Charlie"})
        resp = client.get("/api/contacts")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Alice" in names
        assert "Charlie" in names

    def test_summaries_omit_notes(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        client.post("/api/contacts", json={"name": "Dave", "notes": "secret notes"})
        resp = client.get("/api/contacts")
        assert resp.status_code == 200
        item = next(c for c in resp.json() if c["name"] == "Dave")
        assert "notes" not in item

    def test_tag_filter_and(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        client.post("/api/contacts", json={"name": "Eve", "tags": ["ml", "python"]})
        client.post("/api/contacts", json={"name": "Frank", "tags": ["ml"]})
        resp = client.get("/api/contacts?tag=ml&tag=python")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Eve" in names
        assert "Frank" not in names

    def test_q_search(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        client.post(
            "/api/contacts",
            json={"name": "Grace Huang", "company": "UniqueOrg"},
        )
        client.post("/api/contacts", json={"name": "Henry"})
        resp = client.get("/api/contacts?q=UniqueOrg")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Grace Huang" in names
        assert "Henry" not in names


# ── Tags endpoint ─────────────────────────────────────────────────────────────


class TestRESTContactTags:
    def test_tags_endpoint(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        client.post(
            "/api/contacts",
            json={"name": "Iris", "tags": ["networking", "ml"]},
        )
        resp = client.get("/api/contacts/tags")
        assert resp.status_code == 200
        tags = resp.json()
        assert "networking" in tags
        assert "ml" in tags

    def test_unified_tags_includes_contact_tags(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        client.post(
            "/api/contacts",
            json={"name": "Jack", "tags": ["unique-contact-tag"]},
        )
        resp = client.get("/api/tags")
        assert resp.status_code == 200
        assert "unique-contact-tag" in resp.json()


# ── Patch + Delete ───────────────────────────────────────────────────────────


class TestRESTUpdateDeleteContact:
    def test_patch_updates_fields(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        c = client.post("/api/contacts", json={"name": "Karen"}).json()
        resp = client.patch(
            f"/api/contacts/{c['id']}",
            json={"company": "NewCorp", "tags": ["updated"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["company"] == "NewCorp"
        assert data["tags"] == ["updated"]

    def test_patch_nonexistent_returns_404(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        resp = client.patch("/api/contacts/99999", json={"company": "X"})
        assert resp.status_code == 404

    def test_delete_removes_contact(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        c = client.post("/api/contacts", json={"name": "Leo"}).json()
        del_resp = client.delete(f"/api/contacts/{c['id']}")
        assert del_resp.status_code == 200
        get_resp = client.get(f"/api/contacts/{c['id']}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, db_conn: Connection[Any]) -> None:
        client = _make_contact_client(db_conn)
        resp = client.delete("/api/contacts/99999")
        assert resp.status_code == 404
