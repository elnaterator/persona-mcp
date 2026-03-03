"""ResumeService — shared business logic for resume version CRUD operations."""

import json
from typing import Any

from persona.database import (
    create_resume_version,
    delete_resume_version,
    load_default_resume_version,
    load_resume_version,
    load_resume_versions,
    set_default_resume_version,
    update_resume_version_data,
    update_resume_version_metadata,
)
from persona.db import DBConnection
from persona.models import (
    ContactInfo,
    Education,
    Skill,
    WorkExperience,
)

SECTION_UPDATE = ("contact", "summary")
SECTION_LIST = ("experience", "education", "skills")
ALL_SECTIONS = ("contact", "summary", "experience", "education", "skills")


class ResumeService:
    """Resume version CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None:
        self._conn = conn

    # --- Version management ---

    def list_resumes(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List all resume versions with metadata."""
        return load_resume_versions(self._conn, user_id=user_id)

    def get_resume(
        self, version_id: int | None = None, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get a resume version. If id is None, returns the default."""
        if version_id is None:
            return load_default_resume_version(self._conn, user_id=user_id)
        return load_resume_version(self._conn, version_id, user_id=user_id)

    def create_resume(self, label: str, user_id: str | None = None) -> dict[str, Any]:
        """Create a new resume version copied from the default.

        If the user has no existing default resume, creates one with empty data.
        """
        if not label or not label.strip():
            raise ValueError("Label must not be empty")
        try:
            default = load_default_resume_version(self._conn, user_id=user_id)
            resume_data = default["resume_data"]
        except ValueError:
            resume_data = {}
        return create_resume_version(
            self._conn, label.strip(), resume_data, user_id=user_id
        )

    def set_default(self, version_id: int, user_id: str | None = None) -> str:
        """Set a resume version as default."""
        label = set_default_resume_version(self._conn, version_id, user_id=user_id)
        return f"Set '{label}' as default resume"

    def delete_resume(self, version_id: int, user_id: str | None = None) -> str:
        """Delete a resume version."""
        label = delete_resume_version(self._conn, version_id, user_id=user_id)
        return f"Deleted resume version '{label}'"

    def update_metadata(
        self, version_id: int, label: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Update resume version label."""
        if not label or not label.strip():
            raise ValueError("Label must not be empty")
        return update_resume_version_metadata(
            self._conn, version_id, label.strip(), user_id=user_id
        )

    # --- Section operations (version-scoped) ---

    def get_section(
        self, section: str, version_id: int | None = None, user_id: str | None = None
    ) -> Any:
        """Get a section from a resume version."""
        if section not in ALL_SECTIONS:
            raise ValueError(
                f"Invalid section: '{section}'. "
                f"Must be one of: {', '.join(ALL_SECTIONS)}"
            )
        version = self.get_resume(version_id, user_id=user_id)
        resume_data = version["resume_data"]
        value = resume_data.get(section)
        return value

    def update_section(
        self,
        section: str,
        data: dict[str, Any],
        version_id: int | None = None,
        user_id: str | None = None,
    ) -> str:
        """Update a singleton section (contact or summary) on a version."""
        if section not in SECTION_UPDATE:
            raise ValueError(
                f"Invalid section for update_section: '{section}'. "
                f"Must be one of: {', '.join(SECTION_UPDATE)}"
            )

        version = self.get_resume(version_id, user_id=user_id)
        vid = version["id"]
        resume_data = version["resume_data"]

        if section == "contact":
            known_fields = set(ContactInfo.model_fields.keys())
            filtered = {k: v for k, v in data.items() if k in known_fields}
            if not filtered:
                raise ValueError("At least one contact field must be provided")
            existing = resume_data.get("contact", {})
            existing.update(filtered)
            resume_data["contact"] = existing
            update_resume_version_data(self._conn, vid, resume_data)
            return f"Updated contact fields: {', '.join(filtered.keys())}"

        # summary
        text = data.get("text", "")
        if not text:
            raise ValueError("Summary text must not be empty")
        resume_data["summary"] = text
        update_resume_version_data(self._conn, vid, resume_data)
        return "Updated summary"

    def add_entry(
        self,
        section: str,
        data: dict[str, Any],
        version_id: int | None = None,
        user_id: str | None = None,
    ) -> str:
        """Add an entry to a list section of a resume version."""
        if section not in SECTION_LIST:
            raise ValueError(
                f"Invalid section for add_entry: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}"
            )

        # Validate entry data by constructing the model
        model_cls = _SECTION_MODELS[section]
        entry = model_cls(**data)

        version = self.get_resume(version_id, user_id=user_id)
        vid = version["id"]
        resume_data = version["resume_data"]

        entries = resume_data.get(section, [])

        # For skills, check for case-insensitive duplicates
        if section == "skills":
            for existing in entries:
                if existing.get("name", "").lower() == entry.name.lower():
                    raise ValueError(
                        f"Skill '{entry.name}' already exists "
                        f"under category '{existing.get('category')}'"
                    )

        # Prepend for experience/education, append for skills
        entry_dict = json.loads(entry.model_dump_json())
        if section in ("experience", "education"):
            entries.insert(0, entry_dict)
        else:
            entries.append(entry_dict)

        resume_data[section] = entries
        update_resume_version_data(self._conn, vid, resume_data)
        return f"Added {section} entry: {_entry_summary(section, entry)}"

    def update_entry(
        self,
        section: str,
        index: int,
        data: dict[str, Any],
        version_id: int | None = None,
        user_id: str | None = None,
    ) -> str:
        """Update an entry in a list section by index."""
        if section not in SECTION_LIST:
            raise ValueError(
                f"Invalid section for update_entry: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}"
            )

        version = self.get_resume(version_id, user_id=user_id)
        vid = version["id"]
        resume_data = version["resume_data"]
        entries = resume_data.get(section, [])

        if index < 0 or index >= len(entries):
            raise ValueError(
                f"{section.title()} index {index} out of range. "
                f"Resume has {len(entries)} {section} entries."
            )

        model_cls = _SECTION_MODELS[section]
        existing = model_cls(**entries[index])
        updated = existing.model_copy(update=data)
        entries[index] = json.loads(updated.model_dump_json())

        resume_data[section] = entries
        update_resume_version_data(self._conn, vid, resume_data)
        return (
            f"Updated {section} entry at index {index}: "
            f"{_entry_summary(section, updated)}"
        )

    def remove_entry(
        self,
        section: str,
        index: int,
        version_id: int | None = None,
        user_id: str | None = None,
    ) -> str:
        """Remove an entry from a list section by index."""
        if section not in SECTION_LIST:
            raise ValueError(
                f"Invalid section for remove_entry: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}"
            )

        version = self.get_resume(version_id, user_id=user_id)
        vid = version["id"]
        resume_data = version["resume_data"]
        entries = resume_data.get(section, [])

        if index < 0 or index >= len(entries):
            raise ValueError(
                f"{section.title()} index {index} out of range. "
                f"Resume has {len(entries)} {section} entries."
            )

        model_cls = _SECTION_MODELS[section]
        removed = model_cls(**entries[index])
        entries.pop(index)

        resume_data[section] = entries
        update_resume_version_data(self._conn, vid, resume_data)
        return f"Removed {section} entry: {_entry_summary(section, removed)}"


_SECTION_MODELS: dict[str, type] = {
    "experience": WorkExperience,
    "education": Education,
    "skills": Skill,
}


def _entry_summary(section: str, entry: WorkExperience | Education | Skill) -> str:
    """Create a short human-readable summary of an entry."""
    if isinstance(entry, WorkExperience):
        return f"{entry.title} at {entry.company}"
    elif isinstance(entry, Education):
        return f"{entry.degree} from {entry.institution}"
    else:
        return f"{entry.name} ({entry.category})"
