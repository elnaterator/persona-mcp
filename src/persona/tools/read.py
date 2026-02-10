"""Read tools for persona MCP server — get_resume, get_resume_section."""

import logging
from pathlib import Path
from typing import Any

from persona.config import RESUME_SUBPATH
from persona.resume_store import load_resume

logger = logging.getLogger("persona")

VALID_SECTIONS = ("contact", "summary", "experience", "education", "skills")


def get_resume(data_dir: Path) -> dict[str, Any]:
    """Get the full resume as structured data."""
    logger.info("get_resume invoked")
    resume_path = data_dir / RESUME_SUBPATH / "resume.md"
    resume = load_resume(resume_path)
    return resume.model_dump()


def get_resume_section(section: str, data_dir: Path) -> Any:
    """Get a specific resume section by name.

    Args:
        section: One of: contact, summary, experience, education, skills.
        data_dir: The persona data directory.

    Raises:
        ValueError: If section name is invalid.
    """
    logger.info("get_resume_section invoked, section=%s", section)
    if section not in VALID_SECTIONS:
        raise ValueError(
            f"Invalid section: '{section}'. Must be one of: {', '.join(VALID_SECTIONS)}"
        )

    resume_data = get_resume(data_dir)
    return resume_data[section]
