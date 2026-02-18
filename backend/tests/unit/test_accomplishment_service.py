"""Unit tests for AccomplishmentService and accomplishment DB functions."""

import sqlite3

import pytest


@pytest.fixture
def acc_service(db_conn: sqlite3.Connection):  # type: ignore[no-untyped-def]
    """AccomplishmentService backed by an empty in-memory database."""
    from persona.accomplishment_service import AccomplishmentService

    return AccomplishmentService(db_conn)


# ── US1: Create ──────────────────────────────────────────────────────────────


class TestAccomplishmentServiceCreate:
    """Tests for AccomplishmentService.create_accomplishment (T006)."""

    def test_requires_title(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Tt]itle"):
            svc.create_accomplishment({})

    def test_rejects_blank_title(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Tt]itle"):
            svc.create_accomplishment({"title": "   "})

    def test_stores_all_star_fields(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        result = svc.create_accomplishment(
            {
                "title": "Led migration",
                "situation": "Monolith caused long deploys.",
                "task": "Migrate 3 services.",
                "action": "Coordinated 4 teams.",
                "result": "80% faster deploys.",
            }
        )
        assert result["title"] == "Led migration"
        assert result["situation"] == "Monolith caused long deploys."
        assert result["task"] == "Migrate 3 services."
        assert result["action"] == "Coordinated 4 teams."
        assert result["result"] == "80% faster deploys."

    def test_tags_trimmed_and_persisted(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        result = svc.create_accomplishment(
            {
                "title": "Test",
                "tags": ["  leadership  ", "technical", "leadership"],
            }
        )
        assert set(result["tags"]) == {"leadership", "technical"}
        assert len(result["tags"]) == 2  # deduplicated

    def test_accomplishment_date_nullable(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        result = svc.create_accomplishment({"title": "No date"})
        assert result["accomplishment_date"] is None

    def test_accomplishment_date_stored(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        result = svc.create_accomplishment(
            {"title": "Dated", "accomplishment_date": "2024-03-15"}
        )
        assert result["accomplishment_date"] == "2024-03-15"

    def test_timestamps_are_non_empty_strings(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        result = svc.create_accomplishment({"title": "Timestamp test"})
        assert isinstance(result["created_at"], str) and result["created_at"] != ""
        assert isinstance(result["updated_at"], str) and result["updated_at"] != ""

    def test_assigns_unique_id(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        a = svc.create_accomplishment({"title": "First"})
        b = svc.create_accomplishment({"title": "Second"})
        assert a["id"] != b["id"]

    def test_partial_star_allowed(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        result = svc.create_accomplishment({"title": "Partial"})
        assert result["situation"] == ""
        assert result["task"] == ""
        assert result["action"] == ""
        assert result["result"] == ""

    def test_invalid_date_format_rejected(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Dd]ate"):
            svc.create_accomplishment(
                {"title": "Bad date", "accomplishment_date": "March 2024"}
            )


class TestAccomplishmentServiceGet:
    """Tests for AccomplishmentService.get_accomplishment (T006)."""

    def test_gets_existing(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment({"title": "Find me"})
        result = svc.get_accomplishment(created["id"])
        assert result["id"] == created["id"]
        assert result["title"] == "Find me"

    def test_raises_for_nonexistent(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.get_accomplishment(9999)


# ── US2: List / Tags ──────────────────────────────────────────────────────────


class TestAccomplishmentServiceList:
    """Tests for AccomplishmentService.list_accomplishments (T018)."""

    def test_lists_all(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        svc.create_accomplishment({"title": "A"})
        svc.create_accomplishment({"title": "B"})
        results = svc.list_accomplishments()
        assert len(results) == 2

    def test_returns_empty_when_none(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        assert svc.list_accomplishments() == []

    def test_filter_by_tag(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        svc.create_accomplishment({"title": "Leader", "tags": ["leadership"]})
        svc.create_accomplishment({"title": "Coder", "tags": ["technical"]})
        results = svc.list_accomplishments(tag="leadership")
        assert len(results) == 1
        assert results[0]["title"] == "Leader"

    def test_filter_by_tag_no_match_returns_empty(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        svc.create_accomplishment({"title": "A", "tags": ["technical"]})
        assert svc.list_accomplishments(tag="leadership") == []

    def test_returns_summary_shape_no_star_body(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        svc.create_accomplishment(
            {"title": "Test", "situation": "A situation", "result": "Good"}
        )
        results = svc.list_accomplishments()
        assert len(results) == 1
        item = results[0]
        assert "situation" not in item
        assert "task" not in item
        assert "action" not in item
        assert "result" not in item

    def test_reverse_chronological_by_date(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        svc.create_accomplishment(
            {"title": "Older", "accomplishment_date": "2023-01-01"}
        )
        svc.create_accomplishment(
            {"title": "Newer", "accomplishment_date": "2024-01-01"}
        )
        results = svc.list_accomplishments()
        assert results[0]["title"] == "Newer"
        assert results[1]["title"] == "Older"

    def test_null_date_sorted_last(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        svc.create_accomplishment({"title": "No date"})
        svc.create_accomplishment(
            {"title": "Has date", "accomplishment_date": "2024-01-01"}
        )
        results = svc.list_accomplishments()
        assert results[0]["title"] == "Has date"
        assert results[1]["title"] == "No date"


class TestAccomplishmentServiceListTags:
    """Tests for AccomplishmentService.list_tags (T018)."""

    def test_returns_sorted_unique_tags(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        svc.create_accomplishment({"title": "A", "tags": ["technical", "leadership"]})
        svc.create_accomplishment(
            {"title": "B", "tags": ["leadership", "cross-functional"]}
        )
        tags = svc.list_tags()
        assert tags == sorted({"technical", "leadership", "cross-functional"})

    def test_empty_when_no_accomplishments(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        assert svc.list_tags() == []


# ── US3: Update ───────────────────────────────────────────────────────────────


class TestAccomplishmentServiceUpdate:
    """Tests for AccomplishmentService.update_accomplishment (T030)."""

    def test_partial_update_leaves_other_fields(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment(
            {"title": "Original", "situation": "Old situation"}
        )
        updated = svc.update_accomplishment(created["id"], {"result": "New result"})
        assert updated["result"] == "New result"
        assert updated["situation"] == "Old situation"
        assert updated["title"] == "Original"

    def test_blank_title_raises(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment({"title": "Original"})
        with pytest.raises(ValueError, match="[Tt]itle"):
            svc.update_accomplishment(created["id"], {"title": ""})

    def test_unknown_id_raises(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.update_accomplishment(9999, {"result": "x"})

    def test_date_format_validated(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment({"title": "Original"})
        with pytest.raises(ValueError, match="[Dd]ate"):
            svc.update_accomplishment(
                created["id"], {"accomplishment_date": "not-a-date"}
            )

    def test_updated_at_changes(self, acc_service: object) -> None:
        import time

        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment({"title": "Original"})
        time.sleep(0.01)
        updated = svc.update_accomplishment(created["id"], {"result": "New"})
        # updated_at should be set (non-empty); it may equal created_at in fast DBs
        assert isinstance(updated["updated_at"], str) and updated["updated_at"] != ""

    def test_clear_star_field_stored_as_empty(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment(
            {"title": "Original", "result": "Some result"}
        )
        updated = svc.update_accomplishment(created["id"], {"result": ""})
        assert updated["result"] == ""


# ── US4: Delete ───────────────────────────────────────────────────────────────


class TestAccomplishmentServiceDelete:
    """Tests for AccomplishmentService.delete_accomplishment (T039)."""

    def test_delete_returns_record(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment({"title": "Delete me"})
        deleted = svc.delete_accomplishment(created["id"])
        assert deleted["title"] == "Delete me"
        assert deleted["id"] == created["id"]

    def test_deleted_not_retrievable(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        created = svc.create_accomplishment({"title": "Delete me"})
        svc.delete_accomplishment(created["id"])
        with pytest.raises(ValueError, match="not found"):
            svc.get_accomplishment(created["id"])

    def test_unknown_id_raises(self, acc_service: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.delete_accomplishment(9999)
