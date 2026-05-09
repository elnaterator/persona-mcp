"""Contract tests for contact communications REST API."""

from collections.abc import Generator
from typing import Any

import pytest
from psycopg import Connection
from starlette.testclient import TestClient

from persona.auth import current_user_id_var

_USER_A = "comm_api_user_a"
_USER_B = "comm_api_user_b"


@pytest.fixture(autouse=True)
def _set_user_context() -> Generator[None, None, None]:
    token = current_user_id_var.set(_USER_A)
    try:
        yield
    finally:
        current_user_id_var.reset(token)


def _make_client(db_conn: Connection[Any]) -> TestClient:
    from fastapi import FastAPI

    from persona.api.routes import create_router
    from persona.communication_service import ContactCommunicationService
    from persona.contact_service import ContactService
    from persona.resume_service import ResumeService

    svc = ResumeService(db_conn)  # type: ignore[arg-type]
    contact_svc = ContactService(db_conn)  # type: ignore[arg-type]
    comm_svc = ContactCommunicationService(db_conn)  # type: ignore[arg-type]
    app = FastAPI()
    app.include_router(
        create_router(svc, contact_service=contact_svc, comm_service=comm_svc)
    )
    return TestClient(app)


@pytest.fixture
def client(db_conn: Connection[Any]) -> TestClient:
    db_conn.execute(
        "INSERT INTO users (id, email) VALUES (%s, 'a@t.com') "
        "ON CONFLICT (id) DO NOTHING",
        (_USER_A,),
    )
    db_conn.execute(
        "INSERT INTO users (id, email) VALUES (%s, 'b@t.com') "
        "ON CONFLICT (id) DO NOTHING",
        (_USER_B,),
    )
    return _make_client(db_conn)


@pytest.fixture
def contact_id(client: TestClient) -> int:
    resp = client.post("/api/contacts", json={"name": "Test Person"})
    assert resp.status_code == 201
    return resp.json()["id"]


_VALID_COMM = {
    "type": "email",
    "direction": "sent",
    "body": "Hello there",
    "date": "2025-03-10",
    "subject": "Test",
    "status": "sent",
    "tags": ["outreach"],
}


class TestContactCommCRUD:
    def test_list_empty(self, client: TestClient, contact_id: int) -> None:
        resp = client.get(f"/api/contacts/{contact_id}/communications")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_returns_201(self, client: TestClient, contact_id: int) -> None:
        resp = client.post(
            f"/api/contacts/{contact_id}/communications", json=_VALID_COMM
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "email"
        assert data["body"] == "Hello there"
        assert data["tags"] == ["outreach"]
        assert data["contact_ref_id"] == contact_id

    def test_list_after_add(self, client: TestClient, contact_id: int) -> None:
        client.post(f"/api/contacts/{contact_id}/communications", json=_VALID_COMM)
        resp = client.get(f"/api/contacts/{contact_id}/communications")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_patch_updates_fields(self, client: TestClient, contact_id: int) -> None:
        add_resp = client.post(
            f"/api/contacts/{contact_id}/communications", json=_VALID_COMM
        )
        comm_id = add_resp.json()["id"]
        patch_resp = client.patch(
            f"/api/contacts/{contact_id}/communications/{comm_id}",
            json={"subject": "Updated", "tags": ["followup"]},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["subject"] == "Updated"
        assert patch_resp.json()["tags"] == ["followup"]

    def test_delete_removes_comm(self, client: TestClient, contact_id: int) -> None:
        add_resp = client.post(
            f"/api/contacts/{contact_id}/communications", json=_VALID_COMM
        )
        comm_id = add_resp.json()["id"]
        del_resp = client.delete(f"/api/contacts/{contact_id}/communications/{comm_id}")
        assert del_resp.status_code == 200
        list_resp = client.get(f"/api/contacts/{contact_id}/communications")
        assert list_resp.json() == []

    def test_add_invalid_type_returns_422(
        self, client: TestClient, contact_id: int
    ) -> None:
        resp = client.post(
            f"/api/contacts/{contact_id}/communications",
            json={**_VALID_COMM, "type": "fax"},
        )
        assert resp.status_code == 422

    def test_add_invalid_direction_returns_422(
        self, client: TestClient, contact_id: int
    ) -> None:
        resp = client.post(
            f"/api/contacts/{contact_id}/communications",
            json={**_VALID_COMM, "direction": "outbound"},
        )
        assert resp.status_code == 422

    def test_add_contact_not_found_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/contacts/9999/communications", json=_VALID_COMM)
        assert resp.status_code == 404


class TestCommunicationSearch:
    def test_search_empty(self, client: TestClient) -> None:
        resp = client.get("/api/communications")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_finds_by_subject(self, client: TestClient, contact_id: int) -> None:
        client.post(
            f"/api/contacts/{contact_id}/communications",
            json={**_VALID_COMM, "subject": "UniquePhrase"},
        )
        resp = client.get("/api/communications?q=UniquePhrase")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["parent_type"] == "contact"
        assert results[0]["parent_id"] == contact_id
        assert "parent_name" in results[0]

    def test_search_tag_filter(self, client: TestClient, contact_id: int) -> None:
        client.post(
            f"/api/contacts/{contact_id}/communications",
            json={**_VALID_COMM, "tags": ["alpha", "beta"]},
        )
        client.post(
            f"/api/contacts/{contact_id}/communications",
            json={**_VALID_COMM, "tags": ["alpha"]},
        )
        resp = client.get("/api/communications?tag=alpha&tag=beta")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_search_returns_contact_parent_type(
        self, client: TestClient, contact_id: int
    ) -> None:
        client.post(f"/api/contacts/{contact_id}/communications", json=_VALID_COMM)
        resp = client.get("/api/communications")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["parent_type"] == "contact"


class TestCommunicationSearchCrossUserIsolation:
    def test_user_b_cannot_see_user_a_comms_via_service(
        self, db_conn: Connection[Any]
    ) -> None:
        """Service-level isolation: search with user_b id returns no user_a comms."""
        from persona.communication_service import ContactCommunicationService
        from persona.contact_service import ContactService

        # Ensure both users exist in users table
        for uid, email in [(_USER_A, "a2@t.com"), (_USER_B, "b2@t.com")]:
            db_conn.execute(
                "INSERT INTO users (id, email) VALUES (%s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                (uid, email),
            )

        # User A creates contact + comm
        cs_a = ContactService(db_conn)  # type: ignore[arg-type]
        contact = cs_a.create_contact({"name": "User A Contact"}, user_id=_USER_A)
        comm_svc_a = ContactCommunicationService(db_conn)  # type: ignore[arg-type]
        comm_svc_a.add_for_contact(contact["id"], _VALID_COMM, user_id=_USER_A)

        # User B searches — should see nothing via service
        comm_svc_b = ContactCommunicationService(db_conn)  # type: ignore[arg-type]
        results = comm_svc_b.search(user_id=_USER_B)
        assert results == []


class TestUnifiedTagsIncludesCommTags:
    def test_tags_endpoint_includes_comm_tags(
        self, client: TestClient, contact_id: int
    ) -> None:
        client.post(
            f"/api/contacts/{contact_id}/communications",
            json={**_VALID_COMM, "tags": ["comm-unique-tag"]},
        )
        resp = client.get("/api/tags")
        assert resp.status_code == 200
        assert "comm-unique-tag" in resp.json()
