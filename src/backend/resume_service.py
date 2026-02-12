"""ResumeService — shared business logic for resume CRUD operations."""

from typing import Any

from backend.database import (
    add_education,
    add_experience,
    add_skill,
    load_resume,
    remove_education,
    remove_experience,
    remove_skill,
    save_contact,
    save_summary,
    update_education,
    update_experience,
    update_skill,
)
from backend.db import DBConnection
from backend.models import Resume

SECTION_UPDATE = ("contact", "summary")
SECTION_LIST = ("experience", "education", "skills")
ALL_SECTIONS = ("contact", "summary", "experience", "education", "skills")

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


class ResumeService:
    """Resume CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn

    def get_resume(self) -> Resume:
        """Get the full resume."""
        return load_resume(self._conn)

    def get_section(self, section: str) -> Any:
        """Get a single resume section by name.

        Returns dict for contact, str for summary, list for list sections.
        """
        if section not in ALL_SECTIONS:
            raise ValueError(
                f"Invalid section: '{section}'. "
                f"Must be one of: {', '.join(ALL_SECTIONS)}"
            )
        data = load_resume(self._conn)
        value = getattr(data, section)
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if isinstance(value, list):
            return [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in value
            ]
        return value

    def update_section(self, section: str, data: dict[str, Any]) -> str:
        """Update a singleton section (contact or summary)."""
        if section not in SECTION_UPDATE:
            raise ValueError(
                f"Invalid section for update_section: '{section}'. "
                f"Must be one of: {', '.join(SECTION_UPDATE)}"
            )
        if section == "contact":
            save_contact(self._conn, data)
            fields = {
                k
                for k in data
                if k
                in {
                    "name",
                    "email",
                    "phone",
                    "location",
                    "linkedin",
                    "website",
                    "github",
                }
            }
            return f"Updated contact fields: {', '.join(fields)}"
        # summary
        text = data.get("text", "")
        if not text:
            raise ValueError("Summary text must not be empty")
        save_summary(self._conn, text)
        return "Updated summary"

    def add_entry(self, section: str, data: dict[str, Any]) -> str:
        """Add an entry to a list section."""
        if section not in SECTION_LIST:
            raise ValueError(
                f"Invalid section for add_entry: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}"
            )
        add_fn = _ADD_FUNCTIONS[section]
        entry = add_fn(self._conn, data)
        return f"Added {section} entry: {entry}"

    def update_entry(self, section: str, index: int, data: dict[str, Any]) -> str:
        """Update an entry in a list section by index."""
        if section not in SECTION_LIST:
            raise ValueError(
                f"Invalid section for update_entry: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}"
            )
        update_fn = _UPDATE_FUNCTIONS[section]
        updated = update_fn(self._conn, index, data)
        return f"Updated {section} entry at index {index}: {updated}"

    def remove_entry(self, section: str, index: int) -> str:
        """Remove an entry from a list section by index."""
        if section not in SECTION_LIST:
            raise ValueError(
                f"Invalid section for remove_entry: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}"
            )
        remove_fn = _REMOVE_FUNCTIONS[section]
        removed = remove_fn(self._conn, index)
        return f"Removed {section} entry: {removed}"
