"""MCP tool handlers for personal context note management."""

from typing import Any

from fastmcp import FastMCP

from persona.auth import require_user_id
from persona.note_service import NoteService


def register_note_tools(mcp: FastMCP, get_service: Any) -> None:
    """Register note MCP tools on the given FastMCP instance."""

    @mcp.tool()
    def list_notes(
        tag: str | None = None, q: str | None = None
    ) -> list[dict[str, Any]]:
        """List personal context notes as summaries (content omitted).

        Args:
            tag: Filter by exact tag (e.g., "python"). Returns only
                notes that include this tag.
            q: Case-insensitive substring search across title and content.
                Multiple words are AND-matched.
        """
        user_id = require_user_id()
        service: NoteService = get_service()
        return service.list_notes(tag=tag, q=q, user_id=user_id)

    @mcp.tool()
    def get_note(id: int) -> dict[str, Any] | str:
        """Get full detail for a specific note including content.

        Args:
            id: Note ID.
        """
        user_id = require_user_id()
        service: NoteService = get_service()
        try:
            return service.get_note(id, user_id=user_id)
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def create_note(
        title: str,
        content: str = "",
        tags: list[str] | None = None,
    ) -> str:
        """Create a new personal context note.

        Args:
            title: Short title for the note (required).
            content: Note body text (optional).
            tags: Category tags (e.g., ["python", "async"]).
        """
        user_id = require_user_id()
        service: NoteService = get_service()
        try:
            note = service.create_note(
                {
                    "title": title,
                    "content": content,
                    "tags": tags or [],
                },
                user_id=user_id,
            )
            return f"Created note '{note['title']}' (id={note['id']})"
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def update_note(
        id: int,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Update fields of an existing note (partial update).

        Only provided fields are changed; omitted fields retain their current values.

        Args:
            id: Note ID.
            title: New title (must not be blank if provided).
            content: Updated body text.
            tags: Updated tag list (replaces existing tags).
        """
        user_id = require_user_id()
        service: NoteService = get_service()
        data: dict[str, Any] = {}
        for field, value in [
            ("title", title),
            ("content", content),
            ("tags", tags),
        ]:
            if value is not None:
                data[field] = value
        try:
            service.update_note(id, data, user_id=user_id)
            return f"Updated note {id}"
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def delete_note(id: int) -> str:
        """Delete a personal context note by ID.

        Args:
            id: Note ID.
        """
        user_id = require_user_id()
        service: NoteService = get_service()
        try:
            note = service.delete_note(id, user_id=user_id)
            return f"Deleted note '{note['title']}' (id={id})"
        except ValueError as e:
            return f"Error: {e}"
