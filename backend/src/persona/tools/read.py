"""Read tools for persona MCP server — get_resume, get_resume_section."""

import logging
from typing import Any

from persona.database import load_resume
from persona.db import DBConnection

logger = logging.getLogger("persona")

VALID_SECTIONS = ("contact", "summary", "experience", "education", "skills")


def get_resume(conn: DBConnection) -> dict[str, Any]:
    """Get the full resume as structured data."""
    logger.info("get_resume invoked")
    resume = load_resume(conn)
    return resume.model_dump()


def get_resume_section(section: str, conn: DBConnection) -> Any:
    """Get a specific resume section by name.

    Args:
        section: One of: contact, summary, experience, education, skills.
        conn: SQLite database connection.

    Raises:
        ValueError: If section name is invalid.
    """
    logger.info("get_resume_section invoked, section=%s", section)
    if section not in VALID_SECTIONS:
        raise ValueError(
            f"Invalid section: '{section}'. Must be one of: {', '.join(VALID_SECTIONS)}"
        )

    resume_data = get_resume(conn)
    return resume_data[section]
