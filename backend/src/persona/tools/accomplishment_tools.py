"""MCP tool handlers for career accomplishment management."""

from typing import Any

from fastmcp import FastMCP

from persona.accomplishment_service import AccomplishmentService


def register_accomplishment_tools(mcp: FastMCP, get_service: Any) -> None:
    """Register accomplishment MCP tools on the given FastMCP instance."""

    @mcp.tool()
    def list_accomplishments(
        tag: str | None = None, q: str | None = None
    ) -> list[dict[str, Any]]:
        """List career accomplishments as summaries (no STAR body fields).

        Args:
            tag: Filter by exact tag (e.g., "leadership"). Returns only
                accomplishments that include this tag.
            q: Case-insensitive substring search across title and STAR fields.
        """
        service: AccomplishmentService = get_service()
        return service.list_accomplishments(tag=tag, q=q)

    @mcp.tool()
    def get_accomplishment(id: int) -> dict[str, Any] | str:
        """Get full STAR detail for a specific accomplishment.

        Args:
            id: Accomplishment ID.
        """
        service: AccomplishmentService = get_service()
        try:
            return service.get_accomplishment(id)
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def create_accomplishment(
        title: str,
        situation: str = "",
        task: str = "",
        action: str = "",
        result: str = "",
        accomplishment_date: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Create a new career accomplishment in STAR format.

        Args:
            title: Brief title of the accomplishment (required).
            situation: Context or background of the achievement.
            task: Your specific responsibility or goal.
            action: Steps you took to address the situation.
            result: Outcome or impact, ideally with metrics.
            accomplishment_date: Date of the achievement (YYYY-MM-DD).
            tags: Category tags (e.g., ["leadership", "technical"]).
        """
        service: AccomplishmentService = get_service()
        try:
            acc = service.create_accomplishment(
                {
                    "title": title,
                    "situation": situation,
                    "task": task,
                    "action": action,
                    "result": result,
                    "accomplishment_date": accomplishment_date,
                    "tags": tags or [],
                }
            )
            return f"Created accomplishment '{acc['title']}' (id={acc['id']})"
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def update_accomplishment(
        id: int,
        title: str | None = None,
        situation: str | None = None,
        task: str | None = None,
        action: str | None = None,
        result: str | None = None,
        accomplishment_date: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Update fields of an existing accomplishment (partial update).

        Only provided fields are changed; omitted fields retain their current values.

        Args:
            id: Accomplishment ID.
            title: New title (must not be blank if provided).
            situation: Updated situation/context.
            task: Updated task/responsibility.
            action: Updated action/steps taken.
            result: Updated result/outcome.
            accomplishment_date: Updated date (YYYY-MM-DD) or None to clear.
            tags: Updated tag list (replaces existing tags).
        """
        service: AccomplishmentService = get_service()
        data: dict[str, Any] = {}
        for field, value in [
            ("title", title),
            ("situation", situation),
            ("task", task),
            ("action", action),
            ("result", result),
            ("accomplishment_date", accomplishment_date),
            ("tags", tags),
        ]:
            if value is not None:
                data[field] = value
        try:
            service.update_accomplishment(id, data)
            return f"Updated accomplishment {id}"
        except ValueError as e:
            return f"Error: {e}"

    @mcp.tool()
    def delete_accomplishment(id: int) -> str:
        """Delete a career accomplishment by ID.

        Args:
            id: Accomplishment ID.
        """
        service: AccomplishmentService = get_service()
        try:
            acc = service.delete_accomplishment(id)
            return f"Deleted accomplishment '{acc['title']}' (id={id})"
        except ValueError as e:
            return f"Error: {e}"
