"""Write tools for persona MCP server — update_section, add/update/remove_entry."""

import logging
from typing import Any

from pydantic import ValidationError

from persona.database import (
    add_education,
    add_experience,
    add_skill,
    remove_education,
    remove_experience,
    remove_skill,
    save_contact,
    save_summary,
    update_education,
    update_experience,
    update_skill,
)
from persona.db import DBConnection
from persona.models import Education, Skill, WorkExperience

logger = logging.getLogger("persona")

SECTION_UPDATE = ("contact", "summary")
SECTION_LIST = ("experience", "education", "skills")

_LIST_MODELS: dict[str, type[WorkExperience | Education | Skill]] = {
    "experience": WorkExperience,
    "education": Education,
    "skills": Skill,
}

_ADD_FUNCTIONS = {
    "experience": add_experience,
    "education": add_education,
    "skills": add_skill,
}

_UPDATE_FUNCTIONS = {
    "experience": update_experience,
    "education": update_education,
    "skills": update_skill,
}

_REMOVE_FUNCTIONS = {
    "experience": remove_experience,
    "education": remove_education,
    "skills": remove_skill,
}


def update_section(section: str, data: dict[str, Any], conn: DBConnection) -> str:
    """Update a non-list section (contact or summary)."""
    logger.info("update_section invoked, section=%s", section)
    if section not in SECTION_UPDATE:
        raise ValueError(
            f"Invalid section for update_section: '{section}'. "
            f"Must be one of: {', '.join(SECTION_UPDATE)}"
        )

    if section == "contact":
        contact_fields = {
            "name",
            "email",
            "phone",
            "location",
            "linkedin",
            "website",
            "github",
        }
        filtered = {k: v for k, v in data.items() if k in contact_fields}
        save_contact(conn, data)
        return f"Updated contact fields: {', '.join(filtered.keys())}"

    # summary
    text = data.get("text", "")
    if not text:
        raise ValueError("Summary text must not be empty")
    save_summary(conn, text)
    return "Updated summary"


def add_entry(section: str, data: dict[str, Any], conn: DBConnection) -> str:
    """Add an entry to a list-based section."""
    logger.info("add_entry invoked, section=%s", section)
    if section not in SECTION_LIST:
        raise ValueError(
            f"Invalid section for add_entry: '{section}'. "
            f"Must be one of: {', '.join(SECTION_LIST)}"
        )

    add_fn = _ADD_FUNCTIONS[section]

    try:
        entry = add_fn(conn, data)
    except (ValidationError, TypeError) as e:
        if isinstance(e, ValidationError):
            fields = [err["loc"][0] for err in e.errors() if err["loc"]]
            names = ", ".join(str(f) for f in fields)
            raise ValueError(f"Missing required fields for {section}: {names}") from e
        raise
    except ValueError:
        raise

    return f"Added {section} entry: {_entry_summary(section, entry)}"


def update_entry(
    section: str, index: int, data: dict[str, Any], conn: DBConnection
) -> str:
    """Update an entry in a list-based section by index."""
    logger.info("update_entry invoked, section=%s, index=%d", section, index)
    if section not in SECTION_LIST:
        raise ValueError(
            f"Invalid section for update_entry: '{section}'. "
            f"Must be one of: {', '.join(SECTION_LIST)}"
        )

    if not data:
        raise ValueError("At least one field must be provided to update")

    update_fn = _UPDATE_FUNCTIONS[section]
    updated = update_fn(conn, index, data)

    summary = _entry_summary(section, updated)
    return f"Updated {section} entry at index {index}: {summary}"


def remove_entry(section: str, index: int, conn: DBConnection) -> str:
    """Remove an entry from a list-based section by index."""
    logger.info("remove_entry invoked, section=%s, index=%d", section, index)
    if section not in SECTION_LIST:
        raise ValueError(
            f"Invalid section for remove_entry: '{section}'. "
            f"Must be one of: {', '.join(SECTION_LIST)}"
        )

    remove_fn = _REMOVE_FUNCTIONS[section]
    removed = remove_fn(conn, index)

    return f"Removed {section} entry: {_entry_summary(section, removed)}"


def _entry_summary(section: str, entry: WorkExperience | Education | Skill) -> str:
    """Create a short human-readable summary of an entry."""
    if section == "experience":
        assert isinstance(entry, WorkExperience)
        return f"{entry.title} at {entry.company}"
    elif section == "education":
        assert isinstance(entry, Education)
        return f"{entry.degree} from {entry.institution}"
    else:
        assert isinstance(entry, Skill)
        return f"{entry.name} ({entry.category})"
