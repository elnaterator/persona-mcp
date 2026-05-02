"""MCP tool handlers for networking contact management."""

from typing import Any

from fastmcp import FastMCP

from persona.auth import require_user_id
from persona.contact_service import ContactService


def register_contact_tools(mcp: FastMCP, get_service: Any) -> None:
    """Register contact MCP tools on the given FastMCP instance."""

    @mcp.tool()
    def list_contacts(
        tag: str | None = None, q: str | None = None
    ) -> list[dict[str, Any]]:
        """List networking contacts as summaries (notes omitted).

        Args:
            tag: Filter by exact tag. Returns only contacts that include this tag.
            q: Case-insensitive substring search across name, company, title, notes.
                Multiple words are AND-matched.
        """
        user_id = require_user_id()
        service: ContactService = get_service()
        return service.list_contacts(tags=[tag] if tag else None, q=q, user_id=user_id)

    @mcp.tool()
    def get_contact(id: int) -> dict[str, Any] | str:
        """Get full detail for a specific contact including notes.

        Args:
            id: Contact ID.
        """
        user_id = require_user_id()
        service: ContactService = get_service()
        try:
            return service.get_contact(id, user_id=user_id)
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def create_contact(
        name: str,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
        title: str | None = None,
        relationship: str | None = None,
        linkedin_url: str | None = None,
        location: str | None = None,
        last_contacted_date: str | None = None,
        followup_date: str | None = None,
        notes: str = "",
        tags: list[str] | None = None,
    ) -> str:
        """Create a new networking contact.

        Args:
            name: Contact's full name (required).
            email: Email address.
            phone: Phone number.
            company: Company or organization.
            title: Job title or role.
            relationship: Relationship type (e.g. Colleague, Recruiter, Mentor).
            linkedin_url: LinkedIn profile URL.
            location: City, region, or country.
            last_contacted_date: Date last contacted (YYYY-MM-DD).
            followup_date: Date to follow up (YYYY-MM-DD).
            notes: Free-form markdown notes about this person.
            tags: Category tags.
        """
        user_id = require_user_id()
        service: ContactService = get_service()
        try:
            contact = service.create_contact(
                {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "company": company,
                    "title": title,
                    "relationship": relationship,
                    "linkedin_url": linkedin_url,
                    "location": location,
                    "last_contacted_date": last_contacted_date,
                    "followup_date": followup_date,
                    "notes": notes,
                    "tags": tags or [],
                },
                user_id=user_id,
            )
            return f"Created contact '{contact['name']}' (id={contact['id']})"
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def update_contact(
        id: int,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
        title: str | None = None,
        relationship: str | None = None,
        linkedin_url: str | None = None,
        location: str | None = None,
        last_contacted_date: str | None = None,
        followup_date: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Update fields of an existing contact (partial update).

        Only provided fields are changed; omitted fields retain their current values.

        Args:
            id: Contact ID.
            name: New name (must not be blank if provided).
            email: Updated email address.
            phone: Updated phone number.
            company: Updated company.
            title: Updated job title.
            relationship: Updated relationship type.
            linkedin_url: Updated LinkedIn URL.
            location: Updated location.
            last_contacted_date: Updated last-contacted date (YYYY-MM-DD).
            followup_date: Updated follow-up date (YYYY-MM-DD).
            notes: Updated free-form notes.
            tags: Updated tag list (replaces existing tags).
        """
        user_id = require_user_id()
        service: ContactService = get_service()
        data: dict[str, Any] = {}
        for field, value in [
            ("name", name),
            ("email", email),
            ("phone", phone),
            ("company", company),
            ("title", title),
            ("relationship", relationship),
            ("linkedin_url", linkedin_url),
            ("location", location),
            ("last_contacted_date", last_contacted_date),
            ("followup_date", followup_date),
            ("notes", notes),
            ("tags", tags),
        ]:
            if value is not None:
                data[field] = value
        try:
            service.update_contact(id, data, user_id=user_id)
            return f"Updated contact {id}"
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def delete_contact(id: int) -> str:
        """Delete a networking contact by ID.

        Args:
            id: Contact ID.
        """
        user_id = require_user_id()
        service: ContactService = get_service()
        try:
            contact = service.delete_contact(id, user_id=user_id)
            return f"Deleted contact '{contact['name']}' (id={id})"
        except ValueError as e:
            return f"Error: {e}"
