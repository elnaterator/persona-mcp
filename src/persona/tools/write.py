"""Write tools for persona MCP server — update_section, add/update/remove_entry."""

import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from persona.config import RESUME_SUBPATH
from persona.models import Education, Skill, WorkExperience
from persona.resume_store import load_resume, save_resume

logger = logging.getLogger("persona")

SECTION_UPDATE = ("contact", "summary")
SECTION_LIST = ("experience", "education", "skills")

# Maps section name to the Pydantic model for validation.
_LIST_MODELS: dict[str, type[WorkExperience | Education | Skill]] = {
    "experience": WorkExperience,
    "education": Education,
    "skills": Skill,
}


def _resume_path(data_dir: Path) -> Path:
    return data_dir / RESUME_SUBPATH / "resume.md"


def update_section(section: str, data: dict[str, Any], data_dir: Path) -> str:
    """Update a non-list section (contact or summary)."""
    logger.info("update_section invoked, section=%s", section)
    if section not in SECTION_UPDATE:
        raise ValueError(
            f"Invalid section for update_section: '{section}'. "
            f"Must be one of: {', '.join(SECTION_UPDATE)}"
        )

    path = _resume_path(data_dir)
    resume = load_resume(path)

    if section == "contact":
        known = set(type(resume.contact).model_fields.keys())
        filtered = {k: v for k, v in data.items() if k in known}
        if not filtered:
            raise ValueError("At least one contact field must be provided")
        updated = resume.contact.model_copy(update=filtered)
        resume.contact = updated
        save_resume(path, resume)
        return f"Updated contact fields: {', '.join(filtered.keys())}"

    # summary
    text = data.get("text", "")
    if not text:
        raise ValueError("Summary text must not be empty")
    resume.summary = text
    save_resume(path, resume)
    return "Updated summary"


def add_entry(section: str, data: dict[str, Any], data_dir: Path) -> str:
    """Add an entry to a list-based section."""
    logger.info("add_entry invoked, section=%s", section)
    if section not in SECTION_LIST:
        raise ValueError(
            f"Invalid section for add_entry: '{section}'. "
            f"Must be one of: {', '.join(SECTION_LIST)}"
        )

    path = _resume_path(data_dir)
    resume = load_resume(path)
    model_cls = _LIST_MODELS[section]

    try:
        entry = model_cls(**data)
    except ValidationError as e:
        fields = [err["loc"][0] for err in e.errors() if err["loc"]]
        names = ", ".join(str(f) for f in fields)
        raise ValueError(f"Missing required fields for {section}: {names}") from e

    entries: list[Any] = getattr(resume, section)

    # Duplicate skill check
    if section == "skills" and isinstance(entry, Skill):
        existing_names = {s.name.lower() for s in entries}
        if entry.name.lower() in existing_names:
            existing = next(s for s in entries if s.name.lower() == entry.name.lower())
            raise ValueError(
                f"Skill '{entry.name}' already exists "
                f"under category '{existing.category}'"
            )

    entries.insert(0, entry)
    save_resume(path, resume)
    return f"Added {section} entry: {_entry_summary(section, entry)}"


def update_entry(section: str, index: int, data: dict[str, Any], data_dir: Path) -> str:
    """Update an entry in a list-based section by index."""
    logger.info("update_entry invoked, section=%s, index=%d", section, index)
    if section not in SECTION_LIST:
        raise ValueError(
            f"Invalid section for update_entry: '{section}'. "
            f"Must be one of: {', '.join(SECTION_LIST)}"
        )

    if not data:
        raise ValueError("At least one field must be provided to update")

    path = _resume_path(data_dir)
    resume = load_resume(path)
    entries: list[Any] = getattr(resume, section)

    if index < 0 or index >= len(entries):
        raise ValueError(
            f"{section.capitalize()} index {index} out of range. "
            f"Resume has {len(entries)} {section} entries."
        )

    existing = entries[index]

    # For skills, handle category=None/empty → "Other"
    if section == "skills" and "category" in data:
        if not data["category"]:
            data["category"] = "Other"

    updated = existing.model_copy(update=data)
    entries[index] = updated
    save_resume(path, resume)
    summary = _entry_summary(section, updated)
    return f"Updated {section} entry at index {index}: {summary}"


def remove_entry(section: str, index: int, data_dir: Path) -> str:
    """Remove an entry from a list-based section by index."""
    logger.info("remove_entry invoked, section=%s, index=%d", section, index)
    if section not in SECTION_LIST:
        raise ValueError(
            f"Invalid section for remove_entry: '{section}'. "
            f"Must be one of: {', '.join(SECTION_LIST)}"
        )

    path = _resume_path(data_dir)
    resume = load_resume(path)
    entries: list[Any] = getattr(resume, section)

    if index < 0 or index >= len(entries):
        raise ValueError(
            f"{section.capitalize()} index {index} out of range. "
            f"Resume has {len(entries)} {section} entries."
        )

    removed = entries.pop(index)
    save_resume(path, resume)
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
