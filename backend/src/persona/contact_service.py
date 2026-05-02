"""ContactService — business logic for networking contact CRUD."""

import re
from typing import Any

from persona.database import (
    create_contact,
    delete_contact,
    load_contact,
    load_contact_tags,
    load_contacts,
    update_contact,
)
from persona.db import DBConnection

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _normalize_tags(tags: list[str]) -> list[str]:
    """Trim whitespace, lowercase, and deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized and normalized not in seen:
            if len(normalized) > 50:
                raise ValueError(f"Tag must not exceed 50 characters: '{normalized}'")
            seen.add(normalized)
            result.append(normalized)
    return result


def _validate_date(value: str | None, field: str) -> str | None:
    if value is not None and value != "" and not _ISO_DATE_RE.match(value):
        raise ValueError(f"{field} must be in YYYY-MM-DD format, got: '{value}'")
    return value or None


class ContactService:
    """Contact CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn

    def list_contacts(
        self,
        tags: list[str] | None = None,
        q: str | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return ContactSummary dicts, ordered by updated_at DESC."""
        normalized = [t.strip().lower() for t in (tags or []) if t.strip()]
        return load_contacts(self._conn, tags=normalized, q=q, user_id=user_id)

    def list_tags(self, user_id: str | None = None) -> list[str]:
        """Return sorted unique tag list for autocomplete."""
        return load_contact_tags(self._conn, user_id=user_id)

    def get_contact(
        self, contact_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Return full Contact dict. Raises ValueError if not found."""
        return load_contact(self._conn, contact_id, user_id=user_id)

    def create_contact(
        self, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Validate and persist a new contact.

        Raises:
            ValueError: If name is missing/blank, or length/format limits exceeded.
        """
        name = data.get("name", "")
        if not name or not str(name).strip():
            raise ValueError("Name is required and must not be blank")
        name = str(name).strip()
        if len(name) > 255:
            raise ValueError("Name must not exceed 255 characters")

        notes = data.get("notes", "")
        if len(notes) > 10000:
            raise ValueError("Notes must not exceed 10000 characters")

        tags = _normalize_tags(data.get("tags", []))

        cleaned: dict[str, Any] = {
            "name": name,
            "notes": notes,
            "tags": tags,
        }
        for field in (
            "email",
            "phone",
            "company",
            "title",
            "relationship",
            "linkedin_url",
            "location",
        ):
            cleaned[field] = data.get(field)

        cleaned["last_contacted_date"] = _validate_date(
            data.get("last_contacted_date"), "last_contacted_date"
        )
        cleaned["followup_date"] = _validate_date(
            data.get("followup_date"), "followup_date"
        )

        return create_contact(self._conn, cleaned, user_id=user_id)

    def update_contact(
        self, contact_id: int, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Patch fields. Raises ValueError if not found or name would become blank."""
        if "name" in data:
            name = data["name"]
            if not str(name).strip():
                raise ValueError("Name must not be blank")
            name = str(name).strip()
            if len(name) > 255:
                raise ValueError("Name must not exceed 255 characters")
            data = {**data, "name": name}

        if "notes" in data and len(data["notes"]) > 10000:
            raise ValueError("Notes must not exceed 10000 characters")

        if "tags" in data and data["tags"] is not None:
            data = {**data, "tags": _normalize_tags(data["tags"])}

        for date_field in ("last_contacted_date", "followup_date"):
            if date_field in data:
                data = {
                    **data,
                    date_field: _validate_date(data[date_field], date_field),
                }

        return update_contact(self._conn, contact_id, data, user_id=user_id)

    def delete_contact(
        self, contact_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Delete. Raises ValueError if not found."""
        return delete_contact(self._conn, contact_id, user_id=user_id)
