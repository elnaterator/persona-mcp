"""Unit tests for ContactService and contact DB functions."""

from typing import Any

import pytest
from psycopg import Connection


@pytest.fixture
def contact_service(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    """ContactService backed by an empty PostgreSQL database."""
    from persona.contact_service import ContactService

    return ContactService(db_conn)  # type: ignore[arg-type]


# ── Create ──────────────────────────────────────────────────────────────────


class TestContactServiceCreate:
    def test_requires_name(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Nn]ame"):
            svc.create_contact({})

    def test_rejects_blank_name(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Nn]ame"):
            svc.create_contact({"name": "   "})

    def test_stores_name(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "Alice Smith"})
        assert result["name"] == "Alice Smith"

    def test_optional_fields_default_none(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "Bob"})
        assert result["email"] is None
        assert result["phone"] is None
        assert result["company"] is None
        assert result["title"] is None
        assert result["relationship"] is None

    def test_notes_defaults_empty(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "Carol"})
        assert result["notes"] == ""

    def test_tags_persisted(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "Dave", "tags": ["recruiter", "ml"]})
        assert set(result["tags"]) == {"recruiter", "ml"}

    def test_timestamps_non_empty(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "Eve"})
        assert result["created_at"]
        assert result["updated_at"]

    def test_rejects_oversized_notes(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="[Nn]otes"):
            svc.create_contact({"name": "Frank", "notes": "x" * 10001})

    def test_rejects_invalid_date_format(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            svc.create_contact({"name": "Grace", "followup_date": "not-a-date"})

    def test_accepts_valid_iso_date(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "Hank", "followup_date": "2025-06-01"})
        assert result["followup_date"] == "2025-06-01"

    def test_accepts_empty_string_date_as_none(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "Iris", "followup_date": ""})
        assert result["followup_date"] is None


# ── Tag normalization ────────────────────────────────────────────────────────


class TestNormalizeTags:
    def test_lowercases_tags(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "X", "tags": ["PYTHON", "ML"]})
        assert result["tags"] == ["python", "ml"]

    def test_trims_whitespace(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "X", "tags": [" golang ", "  rust  "]})
        assert result["tags"] == ["golang", "rust"]

    def test_deduplicates(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        result = svc.create_contact({"name": "X", "tags": ["go", "Go", " go "]})
        assert result["tags"] == ["go"]

    def test_rejects_tag_over_50_chars(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="50"):
            svc.create_contact({"name": "X", "tags": ["a" * 51]})


# ── Update ──────────────────────────────────────────────────────────────────


class TestContactServiceUpdate:
    def test_update_name(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        c = svc.create_contact({"name": "Alice"})
        updated = svc.update_contact(c["id"], {"name": "Alice B"})
        assert updated["name"] == "Alice B"

    def test_rejects_blank_name_on_update(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        c = svc.create_contact({"name": "Alice"})
        with pytest.raises(ValueError, match="[Nn]ame"):
            svc.update_contact(c["id"], {"name": "  "})

    def test_update_not_found(self, contact_service: object) -> None:
        from persona.contact_service import ContactService

        svc: ContactService = contact_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.update_contact(9999, {"name": "X"})
