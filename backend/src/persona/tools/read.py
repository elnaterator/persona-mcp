"""Read tools for persona MCP server — get_resume, get_resume_section."""

import logging
from typing import Any

from persona.auth import current_user_id_var
from persona.db import DBConnection
from persona.models import Resume
from persona.resume_service import ResumeService

logger = logging.getLogger("persona")

VALID_SECTIONS = ("contact", "summary", "experience", "education", "skills")


def get_resume(conn: DBConnection, version_id: int | None = None) -> dict[str, Any]:
    """Get a resume version as structured data. None=default."""
    logger.info("get_resume invoked, version_id=%s", version_id)
    user_id = current_user_id_var.get()
    service = ResumeService(conn)
    version = service.get_resume(version_id, user_id=user_id)
    # Normalize through Resume model to ensure all fields present
    resume = Resume(**version["resume_data"])
    return resume.model_dump()


def get_resume_for_user(
    conn: DBConnection, version_id: int | None = None
) -> dict[str, Any]:
    """Get resume using user_id from ContextVar.

    Raises RuntimeError if no user context.
    """
    user_id = current_user_id_var.get()
    if user_id is None:
        raise RuntimeError("No user context set — cannot access resume data")
    service = ResumeService(conn)
    version = service.get_resume(version_id, user_id=user_id)
    resume = Resume(**version["resume_data"])
    return resume.model_dump()


def get_resume_section(
    section: str, conn: DBConnection, version_id: int | None = None
) -> Any:
    """Get a specific resume section by name.

    Args:
        section: One of: contact, summary, experience, education, skills.
        conn: SQLite database connection.
        version_id: Optional resume version ID (None=default).

    Raises:
        ValueError: If section name is invalid.
    """
    logger.info("get_resume_section invoked, section=%s", section)
    if section not in VALID_SECTIONS:
        raise ValueError(
            f"Invalid section: '{section}'. Must be one of: {', '.join(VALID_SECTIONS)}"
        )

    data = get_resume(conn, version_id)
    return data[section]
