"""AccomplishmentService — business logic for career accomplishment CRUD."""

import re
from typing import Any

from persona.database import (
    create_accomplishment,
    delete_accomplishment,
    load_accomplishment,
    load_accomplishment_tags,
    load_accomplishments,
    update_accomplishment,
)
from persona.db import DBConnection

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(value: str) -> None:
    """Raise ValueError if value is not a YYYY-MM-DD date string."""
    if not _DATE_RE.match(value):
        raise ValueError(
            f"Invalid accomplishment_date '{value}'. Expected format: YYYY-MM-DD"
        )


def _normalize_tags(tags: list[str]) -> list[str]:
    """Trim whitespace from each tag and deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = tag.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


class AccomplishmentService:
    """Accomplishment CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn

    def list_accomplishments(
        self, tag: str | None = None, q: str | None = None
    ) -> list[dict[str, Any]]:
        """Return AccomplishmentSummary dicts, ordered reverse-chronologically."""
        return load_accomplishments(self._conn, tag=tag, q=q)

    def list_tags(self) -> list[str]:
        """Return sorted unique tag list for autocomplete."""
        return load_accomplishment_tags(self._conn)

    def get_accomplishment(self, acc_id: int) -> dict[str, Any]:
        """Return full Accomplishment dict. Raises ValueError if not found."""
        return load_accomplishment(self._conn, acc_id)

    def create_accomplishment(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate and persist a new accomplishment.

        Raises:
            ValueError: If title is missing or blank, or date format is invalid.
        """
        title = data.get("title", "")
        if not title or not str(title).strip():
            raise ValueError("Title is required and must not be blank")

        acc_date = data.get("accomplishment_date")
        if acc_date is not None:
            _validate_date(str(acc_date))

        tags = _normalize_tags(data.get("tags", []))

        cleaned: dict[str, Any] = {
            "title": str(title).strip(),
            "situation": data.get("situation", ""),
            "task": data.get("task", ""),
            "action": data.get("action", ""),
            "result": data.get("result", ""),
            "accomplishment_date": acc_date,
            "tags": tags,
        }
        return create_accomplishment(self._conn, cleaned)

    def update_accomplishment(
        self, acc_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Patch fields. Raises ValueError if not found or title would become empty.

        Only fields present in data are updated. Absent keys are left unchanged.
        """
        if "title" in data:
            title = data["title"]
            if not str(title).strip():
                raise ValueError("Title must not be blank")
            data = {**data, "title": str(title).strip()}

        if "accomplishment_date" in data and data["accomplishment_date"] is not None:
            _validate_date(str(data["accomplishment_date"]))

        if "tags" in data and data["tags"] is not None:
            data = {**data, "tags": _normalize_tags(data["tags"])}

        return update_accomplishment(self._conn, acc_id, data)

    def delete_accomplishment(self, acc_id: int) -> dict[str, Any]:
        """Delete. Raises ValueError if not found."""
        return delete_accomplishment(self._conn, acc_id)
