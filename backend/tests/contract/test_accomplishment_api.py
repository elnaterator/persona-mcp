"""Contract tests for accomplishment REST API and MCP tools.

Tests are grouped by user story. Each story's MCP contract tests appear
BEFORE the tool implementations (TDD per Constitution III).
"""

import sqlite3
from collections.abc import Generator
from typing import Any

import pytest
from starlette.testclient import TestClient

# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def acc_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory DB for accomplishment API tests."""
    from persona.migrations import apply_migrations

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    apply_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture
def acc_service(acc_db: sqlite3.Connection) -> Any:
    """AccomplishmentService for use in MCP tool tests."""
    from persona.accomplishment_service import AccomplishmentService

    return AccomplishmentService(acc_db)


def _make_acc_client(acc_db: sqlite3.Connection) -> TestClient:
    """TestClient with accomplishment routes enabled."""
    from fastapi import FastAPI

    from persona.accomplishment_service import AccomplishmentService
    from persona.api.routes import create_router
    from persona.resume_service import ResumeService

    svc = ResumeService(acc_db)
    app_acc_svc = AccomplishmentService(acc_db)
    app = FastAPI()
    app.include_router(create_router(svc, acc_service=app_acc_svc))
    return TestClient(app)


# ── US1: Record a New Accomplishment ─────────────────────────────────────────


class TestMCPCreateGetAccomplishment:
    """T008 — MCP contract tests for create_accomplishment + get_accomplishment."""

    def test_create_returns_confirmation_string(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        # Call the underlying function directly
        tool_fn = _get_tool_fn(mcp, "create_accomplishment")
        result = tool_fn(
            title="Led platform migration",
            situation="Monolith",
            task="",
            action="",
            result="",
            accomplishment_date=None,
            tags=[],
        )
        assert isinstance(result, str)
        assert "Led platform migration" in result
        assert "id=" in result

    def test_create_missing_title_returns_error_string(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        tool_fn = _get_tool_fn(mcp, "create_accomplishment")
        result = tool_fn(
            title="",
            situation="",
            task="",
            action="",
            result="",
            accomplishment_date=None,
            tags=[],
        )
        assert isinstance(result, str)
        # No Python traceback exposed
        assert "Traceback" not in result
        assert (
            "Error" in result
            or "error" in result
            or "title" in result.lower()
            or "Title" in result
        )

    def test_get_returns_accomplishment_dict(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        create_fn = _get_tool_fn(mcp, "create_accomplishment")
        get_fn = _get_tool_fn(mcp, "get_accomplishment")

        create_fn(
            title="Test acc",
            situation="",
            task="",
            action="",
            result="",
            accomplishment_date=None,
            tags=[],
        )
        # Get ID from the service
        accs = acc_service.list_accomplishments()
        assert len(accs) == 1
        acc_id = accs[0]["id"]

        result = get_fn(id=acc_id)
        assert isinstance(result, dict)
        assert result["title"] == "Test acc"

    def test_get_unknown_id_returns_error_string(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        tool_fn = _get_tool_fn(mcp, "get_accomplishment")
        result = tool_fn(id=9999)
        assert isinstance(result, str)
        assert "Traceback" not in result


class TestRESTCreateGetAccomplishment:
    """T007 — REST contract tests for POST + GET /api/accomplishments/{id}."""

    def test_post_valid_returns_201(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        resp = client.post(
            "/api/accomplishments",
            json={"title": "Led migration", "situation": "Slow deploys"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Led migration"
        assert data["situation"] == "Slow deploys"
        assert "id" in data

    def test_post_missing_title_returns_422(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        resp = client.post("/api/accomplishments", json={"situation": "No title"})
        assert resp.status_code == 422

    def test_get_by_id_returns_full_record(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        created = client.post(
            "/api/accomplishments",
            json={"title": "Test", "result": "Great outcome"},
        ).json()
        resp = client.get(f"/api/accomplishments/{created['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == created["id"]
        assert data["result"] == "Great outcome"

    def test_get_unknown_id_returns_404(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        resp = client.get("/api/accomplishments/9999")
        assert resp.status_code == 404


# ── US2: View and Browse Accomplishments ─────────────────────────────────────


class TestMCPListAccomplishments:
    """T020 — MCP contract test for list_accomplishments tool."""

    def test_list_no_args_returns_summaries(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        acc_service.create_accomplishment({"title": "A", "tags": ["leadership"]})
        acc_service.create_accomplishment({"title": "B", "tags": ["technical"]})

        list_fn = _get_tool_fn(mcp, "list_accomplishments")
        result = list_fn(tag=None, q=None)
        assert isinstance(result, list)
        assert len(result) == 2
        # Summary shape — no STAR body
        for item in result:
            assert "situation" not in item
            assert "title" in item

    def test_list_with_tag_returns_matching(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        acc_service.create_accomplishment({"title": "Leader", "tags": ["leadership"]})
        acc_service.create_accomplishment({"title": "Coder", "tags": ["technical"]})

        list_fn = _get_tool_fn(mcp, "list_accomplishments")
        result = list_fn(tag="leadership", q=None)
        assert len(result) == 1
        assert result[0]["title"] == "Leader"

    def test_list_empty_returns_empty_list(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        list_fn = _get_tool_fn(mcp, "list_accomplishments")
        result = list_fn(tag=None, q=None)
        assert result == []

    def test_list_no_match_returns_empty_not_error(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        acc_service.create_accomplishment({"title": "A", "tags": ["technical"]})
        list_fn = _get_tool_fn(mcp, "list_accomplishments")
        result = list_fn(tag="nonexistent", q=None)
        assert result == []


class TestRESTListTagsAccomplishments:
    """T019 — REST contract tests for GET /api/accomplishments and /tags."""

    def test_list_returns_summaries(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        client.post("/api/accomplishments", json={"title": "A"})
        client.post("/api/accomplishments", json={"title": "B"})
        resp = client.get("/api/accomplishments")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Summary shape
        for item in data:
            assert "situation" not in item
            assert "title" in item

    def test_list_empty_returns_empty_array(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        resp = client.get("/api/accomplishments")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_filter_by_tag(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        client.post(
            "/api/accomplishments", json={"title": "Leader", "tags": ["leadership"]}
        )
        client.post(
            "/api/accomplishments", json={"title": "Coder", "tags": ["technical"]}
        )
        resp = client.get("/api/accomplishments?tag=leadership")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Leader"

    def test_list_tag_no_match_empty_not_error(
        self, acc_db: sqlite3.Connection
    ) -> None:
        client = _make_acc_client(acc_db)
        client.post("/api/accomplishments", json={"title": "A", "tags": ["technical"]})
        resp = client.get("/api/accomplishments?tag=nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_tags_returns_sorted_unique_list(
        self, acc_db: sqlite3.Connection
    ) -> None:
        client = _make_acc_client(acc_db)
        client.post(
            "/api/accomplishments",
            json={"title": "A", "tags": ["technical", "leadership"]},
        )
        client.post("/api/accomplishments", json={"title": "B", "tags": ["leadership"]})
        resp = client.get("/api/accomplishments/tags")
        assert resp.status_code == 200
        tags = resp.json()
        assert isinstance(tags, list)
        assert set(tags) == {"technical", "leadership"}
        assert tags == sorted(tags)

    def test_get_tags_empty_when_no_accomplishments(
        self, acc_db: sqlite3.Connection
    ) -> None:
        client = _make_acc_client(acc_db)
        resp = client.get("/api/accomplishments/tags")
        assert resp.status_code == 200
        assert resp.json() == []


# ── US3: Edit ─────────────────────────────────────────────────────────────────


class TestMCPUpdateAccomplishment:
    """T032 — MCP contract test for update_accomplishment tool."""

    def test_partial_update_returns_confirmation(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        created = acc_service.create_accomplishment({"title": "Original"})
        update_fn = _get_tool_fn(mcp, "update_accomplishment")
        result = update_fn(
            id=created["id"],
            title=None,
            situation=None,
            task=None,
            action=None,
            result="New result",
            accomplishment_date=None,
            tags=None,
        )
        assert isinstance(result, str)
        assert "Traceback" not in result

    def test_unknown_id_returns_error_string(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        update_fn = _get_tool_fn(mcp, "update_accomplishment")
        result = update_fn(
            id=9999,
            title=None,
            situation=None,
            task=None,
            action=None,
            result="x",
            accomplishment_date=None,
            tags=None,
        )
        assert isinstance(result, str)
        assert "Traceback" not in result

    def test_blank_title_returns_error_string(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        created = acc_service.create_accomplishment({"title": "Original"})
        update_fn = _get_tool_fn(mcp, "update_accomplishment")
        result = update_fn(
            id=created["id"],
            title="",
            situation=None,
            task=None,
            action=None,
            result=None,
            accomplishment_date=None,
            tags=None,
        )
        assert isinstance(result, str)
        assert "Traceback" not in result


class TestRESTUpdateAccomplishment:
    """T031 — REST contract test for PATCH /api/accomplishments/{id}."""

    def test_patch_returns_200_with_updated_record(
        self, acc_db: sqlite3.Connection
    ) -> None:
        client = _make_acc_client(acc_db)
        created = client.post(
            "/api/accomplishments",
            json={"title": "Original", "situation": "Old situation"},
        ).json()
        resp = client.patch(
            f"/api/accomplishments/{created['id']}",
            json={"result": "Updated result"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "Updated result"
        assert data["situation"] == "Old situation"

    def test_patch_unknown_id_returns_404(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        resp = client.patch("/api/accomplishments/9999", json={"result": "x"})
        assert resp.status_code == 404

    def test_patch_blank_title_returns_422(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        created = client.post("/api/accomplishments", json={"title": "Original"}).json()
        resp = client.patch(f"/api/accomplishments/{created['id']}", json={"title": ""})
        assert resp.status_code == 422


# ── US4: Delete ───────────────────────────────────────────────────────────────


class TestMCPDeleteAccomplishment:
    """T041 — MCP contract test for delete_accomplishment tool."""

    def test_delete_returns_confirmation_with_title(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        created = acc_service.create_accomplishment({"title": "Delete me"})
        delete_fn = _get_tool_fn(mcp, "delete_accomplishment")
        result = delete_fn(id=created["id"])
        assert isinstance(result, str)
        assert "Delete me" in result
        assert "Traceback" not in result

    def test_delete_unknown_id_returns_error_string(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        delete_fn = _get_tool_fn(mcp, "delete_accomplishment")
        result = delete_fn(id=9999)
        assert isinstance(result, str)
        assert "Traceback" not in result


class TestRESTDeleteAccomplishment:
    """T040 — REST contract test for DELETE /api/accomplishments/{id}."""

    def test_delete_returns_200_with_message(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        created = client.post(
            "/api/accomplishments", json={"title": "Delete me"}
        ).json()
        resp = client.delete(f"/api/accomplishments/{created['id']}")
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_deleted_not_retrievable(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        created = client.post("/api/accomplishments", json={"title": "Gone"}).json()
        client.delete(f"/api/accomplishments/{created['id']}")
        resp = client.get(f"/api/accomplishments/{created['id']}")
        assert resp.status_code == 404

    def test_second_delete_returns_404(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        created = client.post("/api/accomplishments", json={"title": "Gone"}).json()
        client.delete(f"/api/accomplishments/{created['id']}")
        resp = client.delete(f"/api/accomplishments/{created['id']}")
        assert resp.status_code == 404

    def test_delete_unknown_returns_404(self, acc_db: sqlite3.Connection) -> None:
        client = _make_acc_client(acc_db)
        resp = client.delete("/api/accomplishments/9999")
        assert resp.status_code == 404


# ── US5: MCP cross-tool integration ──────────────────────────────────────────


class TestMCPCrossToolIntegration:
    """T048 — MCP cross-tool integration tests."""

    def test_create_list_update_delete_sequence(self, acc_service: Any) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        create_fn = _get_tool_fn(mcp, "create_accomplishment")
        list_fn = _get_tool_fn(mcp, "list_accomplishments")
        update_fn = _get_tool_fn(mcp, "update_accomplishment")
        delete_fn = _get_tool_fn(mcp, "delete_accomplishment")
        get_fn = _get_tool_fn(mcp, "get_accomplishment")

        # Create
        create_result = create_fn(
            title="Cross-tool test",
            situation="",
            task="",
            action="",
            result="",
            accomplishment_date=None,
            tags=[],
        )
        assert isinstance(create_result, str)
        assert "Traceback" not in create_result

        # List — entry appears
        list_result = list_fn(tag=None, q=None)
        assert len(list_result) == 1
        acc_id = list_result[0]["id"]

        # Update
        update_result = update_fn(
            id=acc_id,
            title=None,
            situation=None,
            task=None,
            action=None,
            result="Updated",
            accomplishment_date=None,
            tags=None,
        )
        assert isinstance(update_result, str)
        assert "Traceback" not in update_result

        # List — verify update reflected (via get)
        get_result = get_fn(id=acc_id)
        assert get_result["result"] == "Updated"

        # Delete
        delete_result = delete_fn(id=acc_id)
        assert isinstance(delete_result, str)
        assert "Traceback" not in delete_result

        # List — entry gone
        list_after = list_fn(tag=None, q=None)
        assert list_after == []

    def test_all_error_responses_are_strings_without_traceback(
        self, acc_service: Any
    ) -> None:
        from fastmcp import FastMCP

        from persona.tools.accomplishment_tools import register_accomplishment_tools

        mcp = FastMCP("test")
        register_accomplishment_tools(mcp, lambda: acc_service)

        get_fn = _get_tool_fn(mcp, "get_accomplishment")
        update_fn = _get_tool_fn(mcp, "update_accomplishment")
        delete_fn = _get_tool_fn(mcp, "delete_accomplishment")
        create_fn = _get_tool_fn(mcp, "create_accomplishment")

        errors = [
            get_fn(id=9999),
            update_fn(
                id=9999,
                title=None,
                situation=None,
                task=None,
                action=None,
                result="x",
                accomplishment_date=None,
                tags=None,
            ),
            delete_fn(id=9999),
            create_fn(
                title="",
                situation="",
                task="",
                action="",
                result="",
                accomplishment_date=None,
                tags=[],
            ),
        ]
        for err in errors:
            assert isinstance(err, str), f"Expected str, got {type(err)}"
            assert "Traceback" not in err, f"Traceback exposed: {err}"


# ── Helper ────────────────────────────────────────────────────────────────────


def _get_tool_fn(mcp: Any, name: str) -> Any:
    """Extract a registered MCP tool function by name for direct testing."""
    for tool in mcp._tool_manager._tools.values():
        if tool.name == name:
            return tool.fn
    registered = list(mcp._tool_manager._tools.keys())
    raise KeyError(f"MCP tool '{name}' not found. Registered: {registered}")
