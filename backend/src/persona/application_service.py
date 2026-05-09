"""ApplicationService — business logic for job application CRUD operations."""

from typing import Any

from persona.database import (
    create_application,
    delete_application,
    load_application,
    load_application_tags,
    load_applications,
    unlink_all_for,
    update_application,
)
from persona.db import DBConnection
from persona.link_service import LinkService
from persona.models import APPLICATION_STATUSES


def _normalize_tags(tags: list[str]) -> list[str]:
    """Trim, lowercase, enforce 50-char max, deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if not normalized:
            continue
        if len(normalized) > 50:
            raise ValueError(f"Tag must not exceed 50 characters: '{normalized}'")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


class ApplicationService:
    """Application CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn
        self._links = LinkService(conn)

    # --- Application CRUD ---

    def create_application(
        self, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Create a new application."""
        if not data.get("company"):
            raise ValueError("Company is required")
        if not data.get("position"):
            raise ValueError("Position is required")
        status = data.get("status", "Interested")
        if status not in APPLICATION_STATUSES:
            valid = ", ".join(APPLICATION_STATUSES)
            raise ValueError(f"Invalid status: '{status}'. Must be one of: {valid}")
        if "tags" in data and data["tags"] is not None:
            data = {**data, "tags": _normalize_tags(data["tags"])}
        return create_application(self._conn, data, user_id=user_id)

    def get_application(
        self, app_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get a single application by ID."""
        app = load_application(self._conn, app_id, user_id=user_id)
        uid = user_id or "legacy"
        app["links"] = self._links.list_links("application", app_id, uid)
        return app

    def list_applications(
        self,
        status: str | None = None,
        tags: list[str] | None = None,
        q: str | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List applications with optional filter/search."""
        apps = load_applications(
            self._conn, status=status, tags=tags, q=q, user_id=user_id
        )
        if apps:
            uid = user_id or "legacy"
            ids = [a["id"] for a in apps]
            counts = self._links.count_links("application", ids, uid)
            for a in apps:
                a["link_count"] = counts.get(a["id"], 0)
        return apps

    def list_tags(self, user_id: str | None = None) -> list[str]:
        """Return sorted unique tag list for autocomplete."""
        return load_application_tags(self._conn, user_id=user_id)

    def update_application(
        self, app_id: int, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Update application fields."""
        if "status" in data:
            status = data["status"]
            if status not in APPLICATION_STATUSES:
                valid = ", ".join(APPLICATION_STATUSES)
                raise ValueError(f"Invalid status: '{status}'. Must be one of: {valid}")
        if "tags" in data and data["tags"] is not None:
            data = {**data, "tags": _normalize_tags(data["tags"])}
        return update_application(self._conn, app_id, data, user_id=user_id)

    def delete_application(
        self, app_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Delete an application and cascade."""
        unlink_all_for(self._conn, "application", app_id, user_id or "legacy")
        return delete_application(self._conn, app_id, user_id=user_id)

    # --- Context (AI composite) ---

    def get_application_context(
        self, app_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get full context for AI-assisted operations.

        Returns the application plus everything linked to it via the
        cross-resource links registry, grouped by type.
        """
        app = self.get_application(app_id, user_id=user_id)
        return {"application": app, "linked": app["links"]}
