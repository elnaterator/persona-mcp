"""Contract tests for the /api/links endpoints and link embedding in resources."""

from collections.abc import Generator
from typing import Any

import pytest
from psycopg import Connection
from starlette.testclient import TestClient

from persona.auth import current_user_id_var

_TEST_USER = "link_contract_user"
_OTHER_USER = "link_contract_other"


@pytest.fixture(autouse=True)
def _set_user_context() -> Generator[None, None, None]:
    token = current_user_id_var.set(_TEST_USER)
    try:
        yield
    finally:
        current_user_id_var.reset(token)


@pytest.fixture
def seeded_db(db_conn: Connection[Any]) -> Connection[Any]:
    db_conn.execute(
        "INSERT INTO users (id, email) VALUES (%s, %s), (%s, %s) "
        "ON CONFLICT (id) DO NOTHING",
        (_TEST_USER, "c@test.com", _OTHER_USER, "d@test.com"),
    )
    return db_conn


def _make_client(db_conn: Connection[Any]) -> TestClient:
    from fastapi import FastAPI

    from persona.api.routes import create_router
    from persona.application_service import ApplicationService
    from persona.link_service import LinkService
    from persona.note_service import NoteService
    from persona.resume_service import ResumeService

    svc = ResumeService(db_conn)  # type: ignore[arg-type]
    note_svc = NoteService(db_conn)  # type: ignore[arg-type]
    app_svc = ApplicationService(db_conn)  # type: ignore[arg-type]
    link_svc = LinkService(db_conn)  # type: ignore[arg-type]
    app = FastAPI()
    app.include_router(
        create_router(
            svc,
            app_service=app_svc,
            note_service=note_svc,
            link_service=link_svc,
        )
    )
    return TestClient(app)


def _create_note(client: TestClient, title: str = "Test Note") -> int:
    resp = client.post("/api/notes", json={"title": title})
    assert resp.status_code == 201
    return int(resp.json()["id"])


def _create_app(client: TestClient, company: str = "Acme") -> int:
    resp = client.post(
        "/api/applications",
        json={"company": company, "position": "Dev", "status": "Interested"},
    )
    assert resp.status_code == 201
    return int(resp.json()["id"])


def _link_payload(note_id: int, app_id: int) -> dict[str, Any]:
    return {
        "a_type": "note",
        "a_id": note_id,
        "b_type": "application",
        "b_id": app_id,
    }


# ── POST /api/links ───────────────────────────────────────────────────────────


class TestCreateLink:
    def test_returns_201(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        resp = client.post("/api/links", json=_link_payload(note_id, app_id))
        assert resp.status_code == 201

    def test_invalid_type_returns_422(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        resp = client.post(
            "/api/links",
            json={"a_type": "widget", "a_id": 1, "b_type": "note", "b_id": 1},
        )
        assert resp.status_code == 422

    def test_self_link_returns_422(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        resp = client.post(
            "/api/links",
            json={
                "a_type": "note",
                "a_id": note_id,
                "b_type": "note",
                "b_id": note_id,
            },
        )
        assert resp.status_code == 422

    def test_nonexistent_resource_returns_404(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        resp = client.post(
            "/api/links",
            json={
                "a_type": "note",
                "a_id": note_id,
                "b_type": "application",
                "b_id": 99999,
            },
        )
        assert resp.status_code == 404

    def test_idempotent(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        payload = _link_payload(note_id, app_id)
        assert client.post("/api/links", json=payload).status_code == 201
        assert client.post("/api/links", json=payload).status_code == 201


# ── DELETE /api/links ─────────────────────────────────────────────────────────


class TestDeleteLink:
    def test_returns_204(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        client.post("/api/links", json=_link_payload(note_id, app_id))
        resp = client.request(
            "DELETE",
            "/api/links",
            json=_link_payload(note_id, app_id),
        )
        assert resp.status_code == 204

    def test_invalid_type_returns_422(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        resp = client.request(
            "DELETE",
            "/api/links",
            json={"a_type": "bad", "a_id": 1, "b_type": "note", "b_id": 1},
        )
        assert resp.status_code == 422


# ── Links embedded in GET detail ──────────────────────────────────────────────


class TestLinksEmbeddedInDetail:
    def test_note_detail_includes_links_key(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        resp = client.get(f"/api/notes/{note_id}")
        assert resp.status_code == 200
        assert "links" in resp.json()

    def test_linked_app_appears_in_note_detail(
        self, seeded_db: Connection[Any]
    ) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        client.post("/api/links", json=_link_payload(note_id, app_id))
        data = client.get(f"/api/notes/{note_id}").json()
        app_links = data.get("links", {}).get("application", [])
        assert any(r["id"] == app_id for r in app_links)

    def test_linked_note_appears_in_app_detail(
        self, seeded_db: Connection[Any]
    ) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        client.post("/api/links", json=_link_payload(note_id, app_id))
        data = client.get(f"/api/applications/{app_id}").json()
        note_links = data.get("links", {}).get("note", [])
        assert any(r["id"] == note_id for r in note_links)

    def test_unlink_clears_from_detail(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        payload = _link_payload(note_id, app_id)
        client.post("/api/links", json=payload)
        client.request("DELETE", "/api/links", json=payload)
        data = client.get(f"/api/notes/{note_id}").json()
        assert data.get("links", {}).get("application", []) == []


# ── link_count in list ────────────────────────────────────────────────────────


class TestLinkCountInList:
    def test_note_list_includes_link_count(self, seeded_db: Connection[Any]) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        client.post("/api/links", json=_link_payload(note_id, app_id))
        items = client.get("/api/notes").json()
        item = next((i for i in items if i["id"] == note_id), None)
        assert item is not None
        assert item.get("link_count", 0) == 1

    def test_unlinked_note_has_zero_link_count(
        self, seeded_db: Connection[Any]
    ) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client, "No links")
        items = client.get("/api/notes").json()
        item = next((i for i in items if i["id"] == note_id), None)
        assert item is not None
        assert item.get("link_count", 0) == 0

    def test_application_list_includes_link_count(
        self, seeded_db: Connection[Any]
    ) -> None:
        client = _make_client(seeded_db)
        note_id = _create_note(client)
        app_id = _create_app(client)
        client.post("/api/links", json=_link_payload(note_id, app_id))
        items = client.get("/api/applications").json()
        item = next((i for i in items if i["id"] == app_id), None)
        assert item is not None
        assert item.get("link_count", 0) == 1
