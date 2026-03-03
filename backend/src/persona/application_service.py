"""ApplicationService — business logic for job application CRUD operations."""

from typing import Any

from persona.database import (
    create_application,
    create_communication,
    create_contact,
    delete_application,
    delete_communication,
    delete_contact,
    load_application,
    load_applications,
    load_communications,
    load_contacts,
    load_default_resume_version,
    load_resume_version,
    update_application,
    update_communication,
    update_contact,
)
from persona.db import DBConnection
from persona.models import APPLICATION_STATUSES


class ApplicationService:
    """Application CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn

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
        return create_application(self._conn, data, user_id=user_id)

    def get_application(
        self, app_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get a single application by ID."""
        return load_application(self._conn, app_id, user_id=user_id)

    def list_applications(
        self,
        status: str | None = None,
        q: str | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List applications with optional filter/search."""
        return load_applications(self._conn, status=status, q=q, user_id=user_id)

    def update_application(
        self, app_id: int, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Update application fields."""
        if "status" in data:
            status = data["status"]
            if status not in APPLICATION_STATUSES:
                valid = ", ".join(APPLICATION_STATUSES)
                raise ValueError(f"Invalid status: '{status}'. Must be one of: {valid}")
        return update_application(self._conn, app_id, data, user_id=user_id)

    def delete_application(
        self, app_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Delete an application and cascade."""
        return delete_application(self._conn, app_id, user_id=user_id)

    # --- Contact CRUD ---

    def add_contact(self, app_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Add a contact to an application."""
        if not data.get("name"):
            raise ValueError("Contact name is required")
        return create_contact(self._conn, app_id, data)

    def list_contacts(self, app_id: int) -> list[dict[str, Any]]:
        """List contacts for an application."""
        return load_contacts(self._conn, app_id)

    def update_contact(self, contact_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update a contact."""
        return update_contact(self._conn, contact_id, data)

    def remove_contact(self, contact_id: int) -> str:
        """Remove a contact. Returns contact name."""
        return delete_contact(self._conn, contact_id)

    # --- Communication CRUD ---

    def add_communication(self, app_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Add a communication to an application."""
        if not data.get("type"):
            raise ValueError("Communication type is required")
        if not data.get("direction"):
            raise ValueError("Communication direction is required")
        if not data.get("body"):
            raise ValueError("Communication body is required")
        if not data.get("date"):
            raise ValueError("Communication date is required")
        return create_communication(self._conn, app_id, data)

    def list_communications(self, app_id: int) -> list[dict[str, Any]]:
        """List communications for an application."""
        return load_communications(self._conn, app_id)

    def update_communication(
        self, comm_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a communication."""
        return update_communication(self._conn, comm_id, data)

    def remove_communication(self, comm_id: int) -> str:
        """Remove a communication. Returns subject."""
        return delete_communication(self._conn, comm_id)

    # --- Context (AI composite) ---

    def get_application_context(
        self, app_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get full context for AI-assisted operations."""
        app = load_application(self._conn, app_id, user_id=user_id)
        contacts = load_contacts(self._conn, app_id)
        communications = load_communications(self._conn, app_id)

        resume_version = None
        if app.get("resume_version_id"):
            try:
                resume_version = load_resume_version(
                    self._conn, app["resume_version_id"], user_id=user_id
                )
            except ValueError:
                pass

        default_resume = None
        try:
            default_resume = load_default_resume_version(self._conn, user_id=user_id)
        except ValueError:
            pass

        return {
            "application": app,
            "contacts": contacts,
            "communications": communications,
            "resume_version": resume_version,
            "default_resume": default_resume,
        }
