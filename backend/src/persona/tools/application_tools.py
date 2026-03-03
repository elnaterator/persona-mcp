"""MCP tool handlers for job application management."""

from typing import Any

from fastmcp import FastMCP

from persona.application_service import ApplicationService
from persona.auth import require_user_id


def register_application_tools(mcp: FastMCP, get_service: Any) -> None:
    """Register application MCP tools on the given FastMCP instance."""

    @mcp.tool()
    def list_applications(
        status: str | None = None, q: str | None = None
    ) -> list[dict[str, Any]]:
        """List all job applications with optional filtering.

        Args:
            status: Filter by status (exact match).
            q: Search company/position (case-insensitive substring).
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        return service.list_applications(status=status, q=q, user_id=user_id)

    @mcp.tool()
    def get_application(id: int) -> dict[str, Any]:
        """Get full details for a specific application.

        Args:
            id: Application ID.
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        return service.get_application(id, user_id=user_id)

    @mcp.tool()
    def create_application(
        company: str,
        position: str,
        description: str = "",
        status: str = "Interested",
        url: str | None = None,
        notes: str = "",
        resume_version_id: int | None = None,
    ) -> str:
        """Create a new job application.

        Args:
            company: Company name.
            position: Position title.
            description: Job description text.
            status: Initial status (default: Interested).
            url: Job posting URL.
            notes: Free-text notes.
            resume_version_id: Associated resume version.
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        app = service.create_application(
            {
                "company": company,
                "position": position,
                "description": description,
                "status": status,
                "url": url,
                "notes": notes,
                "resume_version_id": resume_version_id,
            },
            user_id=user_id,
        )
        return f"Created application for '{position}' at '{company}' (id={app['id']})"

    @mcp.tool()
    def update_application(
        id: int,
        company: str | None = None,
        position: str | None = None,
        description: str | None = None,
        status: str | None = None,
        url: str | None = None,
        notes: str | None = None,
        resume_version_id: int | None = None,
    ) -> str:
        """Update an existing application's fields.

        Args:
            id: Application ID.
            company: Updated company name.
            position: Updated position title.
            description: Updated job description.
            status: Updated status.
            url: Updated URL.
            notes: Updated notes.
            resume_version_id: Updated resume version.
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        data: dict[str, Any] = {}
        for field, value in [
            ("company", company),
            ("position", position),
            ("description", description),
            ("status", status),
            ("url", url),
            ("notes", notes),
            ("resume_version_id", resume_version_id),
        ]:
            if value is not None:
                data[field] = value
        service.update_application(id, data, user_id=user_id)
        return f"Updated application {id}"

    @mcp.tool()
    def delete_application(id: int) -> str:
        """Delete an application and all associated data (cascade).

        Args:
            id: Application ID.
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        app = service.delete_application(id, user_id=user_id)
        return (
            f"Deleted application '{app['position']}' at "
            f"'{app['company']}' and all associated data"
        )

    @mcp.tool()
    def add_application_contact(
        app_id: int,
        name: str,
        role: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        notes: str = "",
    ) -> str:
        """Add a contact to an application.

        Args:
            app_id: Application ID.
            name: Contact's full name.
            role: Role/title.
            email: Email address.
            phone: Phone number.
            notes: Notes about contact.
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        # Verify ownership of the parent application
        service.get_application(app_id, user_id=user_id)
        contact = service.add_contact(
            app_id,
            {
                "name": name,
                "role": role,
                "email": email,
                "phone": phone,
                "notes": notes,
            },
        )
        return f"Added contact '{contact['name']}'"

    @mcp.tool()
    def update_application_contact(
        id: int,
        name: str | None = None,
        role: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> str:
        """Update a contact's details.

        Args:
            id: Contact ID.
            name: Updated name.
            role: Updated role.
            email: Updated email.
            phone: Updated phone.
            notes: Updated notes.
        """
        require_user_id()
        service: ApplicationService = get_service()
        data: dict[str, Any] = {}
        for field, value in [
            ("name", name),
            ("role", role),
            ("email", email),
            ("phone", phone),
            ("notes", notes),
        ]:
            if value is not None:
                data[field] = value
        service.update_contact(id, data)
        return f"Updated contact {id}"

    @mcp.tool()
    def remove_application_contact(id: int) -> str:
        """Remove a contact from an application.

        Args:
            id: Contact ID.
        """
        require_user_id()
        service: ApplicationService = get_service()
        name = service.remove_contact(id)
        return f"Removed contact '{name}'"

    @mcp.tool()
    def add_communication(
        app_id: int,
        type: str,
        direction: str,
        body: str,
        date: str,
        contact_id: int | None = None,
        subject: str = "",
        status: str = "sent",
    ) -> str:
        """Log a communication for an application.

        Args:
            app_id: Application ID.
            type: email, phone, interview_note, or other.
            direction: sent or received.
            body: Full content.
            date: ISO 8601 date.
            contact_id: Associated contact ID.
            subject: Subject line.
            status: draft, ready, sent, or archived (default: sent).
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        # Verify ownership of the parent application
        service.get_application(app_id, user_id=user_id)
        comm = service.add_communication(
            app_id,
            {
                "type": type,
                "direction": direction,
                "body": body,
                "date": date,
                "contact_id": contact_id,
                "subject": subject,
                "status": status,
            },
        )
        return f"Added communication (id={comm['id']})"

    @mcp.tool()
    def update_communication(
        id: int,
        type: str | None = None,
        direction: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        date: str | None = None,
        contact_id: int | None = None,
        status: str | None = None,
    ) -> str:
        """Update a communication entry.

        Args:
            id: Communication ID.
            type: Updated type.
            direction: Updated direction.
            subject: Updated subject.
            body: Updated body.
            date: Updated date.
            contact_id: Updated contact ref.
            status: Updated status.
        """
        require_user_id()
        service: ApplicationService = get_service()
        data: dict[str, Any] = {}
        for field, value in [
            ("type", type),
            ("direction", direction),
            ("subject", subject),
            ("body", body),
            ("date", date),
            ("contact_id", contact_id),
            ("status", status),
        ]:
            if value is not None:
                data[field] = value
        service.update_communication(id, data)
        return f"Updated communication {id}"

    @mcp.tool()
    def remove_communication(id: int) -> str:
        """Remove a communication entry.

        Args:
            id: Communication ID.
        """
        require_user_id()
        service: ApplicationService = get_service()
        subject = service.remove_communication(id)
        return f"Removed communication '{subject}'"

    @mcp.tool()
    def get_application_context(id: int) -> dict[str, Any]:
        """Get complete context for AI-assisted operations on an application.

        Returns the application, its contacts, communications, associated
        resume version (if any), and the default resume version.

        Args:
            id: Application ID.
        """
        user_id = require_user_id()
        service: ApplicationService = get_service()
        return service.get_application_context(id, user_id=user_id)
