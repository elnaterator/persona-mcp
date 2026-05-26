"""T15: Contract tests for GET /api/search."""

from typing import Any

import pytest
from psycopg import Connection
from starlette.testclient import TestClient

from persona.accomplishment_service import AccomplishmentService
from persona.application_service import ApplicationService
from persona.communication_service import ContactCommunicationService
from persona.contact_service import ContactService
from persona.note_service import NoteService
from persona.resume_service import ResumeService


def _make_client(db_conn: Connection[Any]) -> TestClient:
    from fastapi import FastAPI

    from persona.api.routes import create_router

    svc = ResumeService(db_conn)  # type: ignore[arg-type]
    app_svc = ApplicationService(db_conn)  # type: ignore[arg-type]
    acc_svc = AccomplishmentService(db_conn)  # type: ignore[arg-type]
    note_svc = NoteService(db_conn)  # type: ignore[arg-type]
    contact_svc = ContactService(db_conn)  # type: ignore[arg-type]
    comm_svc = ContactCommunicationService(db_conn)  # type: ignore[arg-type]

    app = FastAPI()
    app.include_router(
        create_router(
            svc,
            app_service=app_svc,
            acc_service=acc_svc,
            note_service=note_svc,
            contact_service=contact_svc,
            comm_service=comm_svc,
        )
    )
    return TestClient(app)


@pytest.fixture
def client_with_data(db_conn: Connection[Any]) -> TestClient:
    """Client backed by DB pre-seeded with cross-resource data."""
    client = _make_client(db_conn)

    # Seed data
    db_conn.execute(
        "INSERT INTO note (user_id, title, content, tags) "
        "VALUES ('legacy', 'Searchable note', 'Contains keyword python', '[]')"
    )
    db_conn.execute(
        "INSERT INTO accomplishment "
        "(user_id, title, situation, task, action, result, tags) "
        "VALUES ('legacy', 'Python refactor', '', '', '', 'reduced lines by 50%', '[]')"
    )
    db_conn.execute(
        "INSERT INTO application "
        "(user_id, company, position, status, tags) "
        "VALUES ('legacy', 'Acme Corp', 'Python Engineer', 'Applied', '[]')"
    )
    return client


class TestSearchEndpointBasic:
    def test_empty_query_returns_empty(self, db_conn: Connection[Any]) -> None:
        client = _make_client(db_conn)
        resp = client.get("/api/search")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_text_search_returns_results(self, client_with_data: TestClient) -> None:
        resp = client_with_data.get("/api/search?q=python")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) >= 1
        titles = [r["title"] for r in results]
        assert any("python" in t.lower() or "Python" in t for t in titles)

    def test_result_shape(self, client_with_data: TestClient) -> None:
        resp = client_with_data.get("/api/search?q=python")
        assert resp.status_code == 200
        results = resp.json()
        for r in results:
            assert "type" in r
            assert "id" in r
            assert "title" in r
            assert "url" in r
            assert "tags" in r

    def test_type_filter(self, client_with_data: TestClient) -> None:
        resp = client_with_data.get("/api/search?q=python&type=note")
        assert resp.status_code == 200
        results = resp.json()
        assert all(r["type"] == "note" for r in results)

    def test_type_filter_multiple(self, client_with_data: TestClient) -> None:
        url = "/api/search?q=python&type=note&type=accomplishment"
        resp = client_with_data.get(url)
        assert resp.status_code == 200
        results = resp.json()
        assert all(r["type"] in {"note", "accomplishment"} for r in results)

    def test_tag_filter(self, db_conn: Connection[Any]) -> None:
        client = _make_client(db_conn)
        db_conn.execute(
            "INSERT INTO note (user_id, title, content, tags) "
            "VALUES ('legacy', 'Tagged note', 'content', '[\"alpha\"]')"
        )
        db_conn.execute(
            "INSERT INTO note (user_id, title, content, tags) "
            "VALUES ('legacy', 'Untagged note', 'content', '[]')"
        )
        resp = client.get("/api/search?tag=alpha")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["title"] == "Tagged note"

    def test_uid_scoping(self, db_conn: Connection[Any]) -> None:
        """Results from one user should not appear for another."""
        from fastapi import FastAPI

        from persona.api.routes import create_router
        from persona.auth import UserContext

        async def _user_a() -> UserContext:
            return UserContext(id="user_a", email="a@test.com", display_name=None)

        async def _user_b() -> UserContext:
            return UserContext(id="user_b", email="b@test.com", display_name=None)

        db_conn.execute(
            "INSERT INTO users (id, email) VALUES (%s, %s), (%s, %s) "
            "ON CONFLICT DO NOTHING",
            ("user_a", "a@test.com", "user_b", "b@test.com"),
        )

        note_svc = NoteService(db_conn)  # type: ignore[arg-type]
        resume_svc = ResumeService(db_conn)  # type: ignore[arg-type]

        app_a = FastAPI()
        app_a.include_router(
            create_router(resume_svc, note_service=note_svc, get_current_user=_user_a)
        )
        client_a = TestClient(app_a, headers={"Authorization": "Bearer tok"})

        app_b = FastAPI()
        app_b.include_router(
            create_router(resume_svc, note_service=note_svc, get_current_user=_user_b)
        )
        client_b = TestClient(app_b, headers={"Authorization": "Bearer tok"})

        # Create note as user_a
        client_a.post("/api/notes", json={"title": "User A note", "content": "scoped"})

        # user_b search should not see user_a's note
        resp = client_b.get("/api/search?q=scoped")
        assert resp.status_code == 200
        assert resp.json() == []

        # user_a search should see it
        resp = client_a.get("/api/search?q=scoped")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
