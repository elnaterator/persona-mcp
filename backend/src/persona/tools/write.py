"""Write tools for persona MCP server — update_section, add/update/remove_entry."""

import logging
from typing import Any

from persona.auth import current_user_id_var
from persona.db import DBConnection
from persona.resume_service import ResumeService

logger = logging.getLogger("persona")

SECTION_UPDATE = ("contact", "summary")
SECTION_LIST = ("experience", "education", "skills")


def update_section(
    section: str,
    data: dict[str, Any],
    conn: DBConnection,
    version_id: int | None = None,
) -> str:
    """Update a non-list section (contact or summary)."""
    logger.info("update_section invoked, section=%s", section)
    user_id = current_user_id_var.get()
    service = ResumeService(conn)
    return service.update_section(section, data, version_id, user_id=user_id)


def add_entry(
    section: str,
    data: dict[str, Any],
    conn: DBConnection,
    version_id: int | None = None,
) -> str:
    """Add an entry to a list-based section."""
    logger.info("add_entry invoked, section=%s", section)
    user_id = current_user_id_var.get()
    service = ResumeService(conn)
    return service.add_entry(section, data, version_id, user_id=user_id)


def update_entry(
    section: str,
    index: int,
    data: dict[str, Any],
    conn: DBConnection,
    version_id: int | None = None,
) -> str:
    """Update an entry in a list-based section by index."""
    logger.info("update_entry invoked, section=%s, index=%d", section, index)
    if not data:
        raise ValueError("At least one field must be provided to update")
    user_id = current_user_id_var.get()
    service = ResumeService(conn)
    return service.update_entry(section, index, data, version_id, user_id=user_id)


def remove_entry(
    section: str,
    index: int,
    conn: DBConnection,
    version_id: int | None = None,
) -> str:
    """Remove an entry from a list-based section by index."""
    logger.info("remove_entry invoked, section=%s, index=%d", section, index)
    user_id = current_user_id_var.get()
    service = ResumeService(conn)
    return service.remove_entry(section, index, version_id, user_id=user_id)


def update_section_for_user(
    section: str,
    data: dict[str, Any],
    conn: DBConnection,
    version_id: int | None = None,
) -> str:
    """Update section using user_id from ContextVar.

    Raises RuntimeError if no user context.
    """
    user_id = current_user_id_var.get()
    if user_id is None:
        raise RuntimeError("No user context set — cannot write resume data")
    service = ResumeService(conn)
    return service.update_section(section, data, version_id, user_id=user_id)
