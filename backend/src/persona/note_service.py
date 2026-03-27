"""NoteService — business logic for personal context note CRUD."""

from typing import Any

from persona.database import (
    create_note,
    delete_note,
    load_note,
    load_note_tags,
    load_notes,
    update_note,
)
from persona.db import DBConnection


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


class NoteService:
    """Note CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn

    def list_notes(
        self, tag: str | None = None, q: str | None = None, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Return NoteSummary dicts, ordered by updated_at DESC."""
        if tag:
            tag = tag.strip().lower()
        return load_notes(self._conn, tag=tag, q=q, user_id=user_id)

    def list_tags(self, user_id: str | None = None) -> list[str]:
        """Return sorted unique tag list for autocomplete."""
        return load_note_tags(self._conn, user_id=user_id)

    def get_note(self, note_id: int, user_id: str | None = None) -> dict[str, Any]:
        """Return full Note dict. Raises ValueError if not found."""
        return load_note(self._conn, note_id, user_id=user_id)

    def create_note(
        self, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Validate and persist a new note.

        Raises:
            ValueError: If title is missing/blank, or length limits exceeded.
        """
        title = data.get("title", "")
        if not title or not str(title).strip():
            raise ValueError("Title is required and must not be blank")

        title = str(title).strip()
        if len(title) > 255:
            raise ValueError("Title must not exceed 255 characters")

        content = data.get("content", "")
        if len(content) > 10000:
            raise ValueError("Content must not exceed 10000 characters")

        tags = _normalize_tags(data.get("tags", []))

        cleaned: dict[str, Any] = {
            "title": title,
            "content": content,
            "tags": tags,
        }
        return create_note(self._conn, cleaned, user_id=user_id)

    def update_note(
        self, note_id: int, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Patch fields. Raises ValueError if not found or title would become empty."""
        if "title" in data:
            title = data["title"]
            if not str(title).strip():
                raise ValueError("Title must not be blank")
            title = str(title).strip()
            if len(title) > 255:
                raise ValueError("Title must not exceed 255 characters")
            data = {**data, "title": title}

        if "content" in data and len(data["content"]) > 10000:
            raise ValueError("Content must not exceed 10000 characters")

        if "tags" in data and data["tags"] is not None:
            data = {**data, "tags": _normalize_tags(data["tags"])}

        return update_note(self._conn, note_id, data, user_id=user_id)

    def delete_note(self, note_id: int, user_id: str | None = None) -> dict[str, Any]:
        """Delete. Raises ValueError if not found."""
        return delete_note(self._conn, note_id, user_id=user_id)
