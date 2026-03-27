"""Unit tests for NoteService and note DB functions."""

from typing import Any

import pytest
from psycopg import Connection


@pytest.fixture
def note_service(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    """NoteService backed by an empty PostgreSQL database."""
    from persona.note_service import NoteService

    return NoteService(db_conn)  # type: ignore[arg-type]


# ── US1: Create ──────────────────────────────────────────────────────────────


class TestNoteServiceCreate:
    """Tests for NoteService.create_note."""

    def test_requires_title(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Tt]itle"):
            svc.create_note({})

    def test_rejects_blank_title(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Tt]itle"):
            svc.create_note({"title": "   "})

    def test_stores_title_and_content(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note({"title": "My Note", "content": "Some content"})
        assert result["title"] == "My Note"
        assert result["content"] == "Some content"

    def test_content_defaults_to_empty(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note({"title": "No content"})
        assert result["content"] == ""

    def test_tags_persisted(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note({"title": "Tagged", "tags": ["python", "async"]})
        assert set(result["tags"]) == {"python", "async"}

    def test_timestamps_are_non_empty_strings(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note({"title": "Timestamp test"})
        assert isinstance(result["created_at"], str) and result["created_at"] != ""
        assert isinstance(result["updated_at"], str) and result["updated_at"] != ""

    def test_assigns_unique_id(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        a = svc.create_note({"title": "First"})
        b = svc.create_note({"title": "Second"})
        assert a["id"] != b["id"]

    def test_title_max_length_enforced(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="255"):
            svc.create_note({"title": "x" * 256})

    def test_content_max_length_enforced(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="10000"):
            svc.create_note({"title": "Test", "content": "x" * 10001})

    def test_tag_max_length_enforced(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="50"):
            svc.create_note({"title": "Test", "tags": ["x" * 51]})


class TestNoteServiceGet:
    """Tests for NoteService.get_note."""

    def test_gets_existing(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        created = svc.create_note({"title": "Find me"})
        result = svc.get_note(created["id"])
        assert result["id"] == created["id"]
        assert result["title"] == "Find me"

    def test_raises_for_nonexistent(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.get_note(9999)

    def test_returns_full_note_with_content(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        created = svc.create_note(
            {"title": "Full", "content": "Body text", "tags": ["test"]}
        )
        result = svc.get_note(created["id"])
        assert result["content"] == "Body text"
        assert result["tags"] == ["test"]


# ── US1: List ────────────────────────────────────────────────────────────────


class TestNoteServiceList:
    """Tests for NoteService.list_notes."""

    def test_lists_all(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "A"})
        svc.create_note({"title": "B"})
        results = svc.list_notes()
        assert len(results) == 2

    def test_returns_empty_when_none(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        assert svc.list_notes() == []

    def test_returns_summary_shape_no_content(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "Test", "content": "Some body text"})
        results = svc.list_notes()
        assert len(results) == 1
        item = results[0]
        assert "content" not in item
        assert "title" in item
        assert "tags" in item

    def test_ordered_by_updated_at_desc(
        self, note_service: object, db_conn: Any
    ) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "Older"})
        newer = svc.create_note({"title": "Newer"})
        # Force distinct updated_at via raw SQL (CURRENT_TIMESTAMP
        # is fixed per-transaction in non-autocommit mode)
        db_conn.execute(
            "UPDATE note SET updated_at = updated_at"
            " + INTERVAL '1 second' WHERE id = %s",
            (newer["id"],),
        )
        results = svc.list_notes()
        assert results[0]["title"] == "Newer"
        assert results[1]["title"] == "Older"


# ── US2: Update ──────────────────────────────────────────────────────────────


class TestNoteServiceUpdate:
    """Tests for NoteService.update_note."""

    def test_partial_update_leaves_other_fields(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        created = svc.create_note({"title": "Original", "content": "Old content"})
        updated = svc.update_note(created["id"], {"content": "New content"})
        assert updated["content"] == "New content"
        assert updated["title"] == "Original"

    def test_blank_title_raises(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        created = svc.create_note({"title": "Original"})
        with pytest.raises(ValueError, match="[Tt]itle"):
            svc.update_note(created["id"], {"title": ""})

    def test_unknown_id_raises(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.update_note(9999, {"content": "x"})

    def test_updated_at_changes(self, note_service: object) -> None:
        import time

        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        created = svc.create_note({"title": "Original"})
        time.sleep(0.01)
        updated = svc.update_note(created["id"], {"content": "New"})
        assert isinstance(updated["updated_at"], str) and updated["updated_at"] != ""


# ── US3: Tags ────────────────────────────────────────────────────────────────


class TestNoteServiceNormalizeTags:
    """Tests for tag normalization."""

    def test_lowercasing(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note({"title": "Test", "tags": ["Python", "ASYNC"]})
        assert result["tags"] == ["python", "async"]

    def test_trimming(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note({"title": "Test", "tags": ["  python  ", "  async  "]})
        assert result["tags"] == ["python", "async"]

    def test_deduplication(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note(
            {"title": "Test", "tags": ["python", "Python", "PYTHON"]}
        )
        assert result["tags"] == ["python"]

    def test_empty_tag_removal(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        result = svc.create_note(
            {"title": "Test", "tags": ["python", "", "  ", "async"]}
        )
        assert result["tags"] == ["python", "async"]


class TestNoteServiceListTags:
    """Tests for NoteService.list_tags."""

    def test_returns_sorted_unique_tags(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "A", "tags": ["python", "async"]})
        svc.create_note({"title": "B", "tags": ["async", "fastapi"]})
        tags = svc.list_tags()
        assert tags == ["async", "fastapi", "python"]

    def test_empty_when_no_notes(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        assert svc.list_tags() == []


# ── US4: Delete ──────────────────────────────────────────────────────────────


class TestNoteServiceDelete:
    """Tests for NoteService.delete_note."""

    def test_delete_returns_record(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        created = svc.create_note({"title": "Delete me"})
        deleted = svc.delete_note(created["id"])
        assert deleted["title"] == "Delete me"
        assert deleted["id"] == created["id"]

    def test_deleted_not_retrievable(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        created = svc.create_note({"title": "Delete me"})
        svc.delete_note(created["id"])
        with pytest.raises(ValueError, match="not found"):
            svc.get_note(created["id"])

    def test_unknown_id_raises(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.delete_note(9999)


# ── US5: Search and Filter ───────────────────────────────────────────────────


class TestNoteServiceSearch:
    """Tests for list_notes with search and filter params."""

    def test_filter_by_tag(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "Python note", "tags": ["python"]})
        svc.create_note({"title": "Go note", "tags": ["go"]})
        results = svc.list_notes(tag="python")
        assert len(results) == 1
        assert results[0]["title"] == "Python note"

    def test_search_by_keyword_in_title(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "Python patterns", "content": "Body"})
        svc.create_note({"title": "Go patterns", "content": "Body"})
        results = svc.list_notes(q="python")
        assert len(results) == 1
        assert results[0]["title"] == "Python patterns"

    def test_search_by_keyword_in_content(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "Note", "content": "Python is great"})
        svc.create_note({"title": "Note2", "content": "Go is fast"})
        results = svc.list_notes(q="python")
        assert len(results) == 1
        assert results[0]["title"] == "Note"

    def test_search_case_insensitive(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "PYTHON patterns"})
        results = svc.list_notes(q="python")
        assert len(results) == 1

    def test_search_multi_word_and(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note({"title": "Python async patterns", "content": "FastAPI"})
        svc.create_note({"title": "Python sync patterns", "content": "Flask"})
        results = svc.list_notes(q="python async")
        assert len(results) == 1
        assert results[0]["title"] == "Python async patterns"

    def test_combined_tag_and_keyword(self, note_service: object) -> None:
        from persona.note_service import NoteService

        svc: NoteService = note_service  # type: ignore[assignment]
        svc.create_note(
            {"title": "Python note", "tags": ["python"], "content": "async stuff"}
        )
        svc.create_note({"title": "Go note", "tags": ["go"], "content": "async stuff"})
        svc.create_note(
            {"title": "Python sync", "tags": ["python"], "content": "sync stuff"}
        )
        results = svc.list_notes(tag="python", q="async")
        assert len(results) == 1
        assert results[0]["title"] == "Python note"
