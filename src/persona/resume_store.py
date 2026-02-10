"""File I/O for resume.md — load and save using python-frontmatter."""

import logging
import re
from pathlib import Path

import frontmatter

from persona.models import (
    ContactInfo,
    Education,
    Resume,
    Skill,
    WorkExperience,
)

logger = logging.getLogger("persona")


def load_resume(path: Path) -> Resume:
    """Load a Resume from a Markdown file with YAML front-matter.

    Returns an empty Resume if the file is missing, empty, or malformed.
    """
    if not path.exists():
        logger.info("Resume file not found at %s, returning empty resume", path)
        return Resume()

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        logger.info("Resume file is empty at %s, returning empty resume", path)
        return Resume()

    try:
        post = frontmatter.loads(text)
    except Exception:
        logger.warning(
            "Failed to parse front-matter in %s, returning empty resume", path
        )
        return Resume()

    contact = _parse_contact(post.metadata)
    body = post.content
    summary = _parse_summary(body)
    experience = _parse_experience(body)
    education = _parse_education(body)
    skills = _parse_skills(body)

    return Resume(
        contact=contact,
        summary=summary,
        experience=experience,
        education=education,
        skills=skills,
    )


def save_resume(path: Path, resume: Resume) -> None:
    """Save a Resume to a Markdown file with YAML front-matter.

    Raises:
        ValueError: If the file cannot be written (permissions, disk full, etc.).
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error("Cannot create directory %s: %s", path.parent, e)
        raise ValueError(f"Cannot create directory for resume: {path.parent}") from e

    metadata = {k: v for k, v in resume.contact.model_dump().items() if v is not None}

    body_parts: list[str] = []

    # Summary
    body_parts.append(
        f"## Summary\n\n{resume.summary}" if resume.summary else "## Summary\n"
    )

    # Experience
    if resume.experience:
        exp_parts = ["## Experience\n"]
        for exp in resume.experience:
            exp_parts.append(_serialize_experience(exp))
        body_parts.append("\n".join(exp_parts))

    # Education
    if resume.education:
        edu_parts = ["## Education\n"]
        for edu in resume.education:
            edu_parts.append(_serialize_education(edu))
        body_parts.append("\n".join(edu_parts))

    # Skills
    if resume.skills:
        body_parts.append(_serialize_skills(resume.skills))

    body = "\n\n".join(body_parts)

    post = frontmatter.Post(body, **metadata)
    try:
        path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    except OSError as e:
        logger.error("Failed to write resume to %s: %s", path, e)
        raise ValueError(f"Failed to save resume: {e}") from e
    logger.info("Resume saved to %s", path)


# --- Parsing helpers ---


def _parse_contact(metadata: dict) -> ContactInfo:
    """Parse contact info from YAML front-matter metadata dict."""
    known_fields = ContactInfo.model_fields.keys()
    filtered = {k: v for k, v in metadata.items() if k in known_fields}
    return ContactInfo(**filtered)


def _extract_section(body: str, heading: str) -> str:
    """Extract content under a ## heading, up to the next ## heading."""
    pattern = rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_summary(body: str) -> str:
    """Parse the ## Summary section."""
    return _extract_section(body, "Summary")


def _parse_experience(body: str) -> list[WorkExperience]:
    """Parse ## Experience section into WorkExperience entries."""
    section = _extract_section(body, "Experience")
    if not section:
        return []

    entries: list[WorkExperience] = []
    # Split by ### headings
    parts = re.split(r"^### ", section, flags=re.MULTILINE)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        entries.append(_parse_experience_entry(part))

    return entries


def _parse_experience_entry(text: str) -> WorkExperience:
    """Parse a single experience entry from ### heading + body."""
    lines = text.split("\n")
    heading = lines[0].strip()

    # Parse "Title | Company" heading
    if "|" in heading:
        title, company = [s.strip() for s in heading.split("|", 1)]
    else:
        title, company = heading, ""

    metadata: dict[str, str | None] = {
        "start_date": None,
        "end_date": None,
        "location": None,
    }
    highlights: list[str] = []

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("- **Start**:"):
            metadata["start_date"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **End**:"):
            metadata["end_date"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **Location**:"):
            metadata["location"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- ") and not stripped.startswith("- **"):
            highlights.append(stripped[2:])

    return WorkExperience(
        title=title,
        company=company,
        start_date=metadata["start_date"],
        end_date=metadata["end_date"],
        location=metadata["location"],
        highlights=highlights,
    )


def _parse_education(body: str) -> list[Education]:
    """Parse ## Education section into Education entries."""
    section = _extract_section(body, "Education")
    if not section:
        return []

    entries: list[Education] = []
    parts = re.split(r"^### ", section, flags=re.MULTILINE)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        entries.append(_parse_education_entry(part))

    return entries


def _parse_education_entry(text: str) -> Education:
    """Parse a single education entry from ### heading + body."""
    lines = text.split("\n")
    heading = lines[0].strip()

    # Parse "Degree | Institution" heading
    if "|" in heading:
        degree, institution = [s.strip() for s in heading.split("|", 1)]
    else:
        degree, institution = heading, ""

    metadata: dict[str, str | None] = {
        "start_date": None,
        "end_date": None,
        "honors": None,
    }

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("- **Start**:"):
            metadata["start_date"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **End**:"):
            metadata["end_date"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **Honors**:"):
            metadata["honors"] = stripped.split(":", 1)[1].strip()

    return Education(
        institution=institution,
        degree=degree,
        start_date=metadata["start_date"],
        end_date=metadata["end_date"],
        honors=metadata["honors"],
    )


def _parse_skills(body: str) -> list[Skill]:
    """Parse ## Skills section into Skill entries grouped by category."""
    section = _extract_section(body, "Skills")
    if not section:
        return []

    skills: list[Skill] = []
    current_category = "Other"

    for line in section.split("\n"):
        stripped = line.strip()
        if stripped.startswith("### "):
            current_category = stripped[4:].strip()
        elif stripped.startswith("- "):
            skill_name = stripped[2:].strip()
            if skill_name:
                skills.append(Skill(name=skill_name, category=current_category))

    return skills


# --- Serialization helpers ---


def _serialize_experience(exp: WorkExperience) -> str:
    """Serialize a WorkExperience to Markdown."""
    lines = [f"### {exp.title} | {exp.company}"]
    if exp.start_date:
        lines.append(f"- **Start**: {exp.start_date}")
    if exp.end_date:
        lines.append(f"- **End**: {exp.end_date}")
    if exp.location:
        lines.append(f"- **Location**: {exp.location}")
    if exp.highlights:
        lines.append("")  # blank line before highlights
        for h in exp.highlights:
            lines.append(f"- {h}")
    return "\n".join(lines)


def _serialize_education(edu: Education) -> str:
    """Serialize an Education to Markdown."""
    lines = [f"### {edu.degree} | {edu.institution}"]
    if edu.start_date:
        lines.append(f"- **Start**: {edu.start_date}")
    if edu.end_date:
        lines.append(f"- **End**: {edu.end_date}")
    if edu.honors:
        lines.append(f"- **Honors**: {edu.honors}")
    return "\n".join(lines)


def _serialize_skills(skills: list[Skill]) -> str:
    """Serialize skills to Markdown grouped by category."""
    categories: dict[str, list[str]] = {}
    for skill in skills:
        cat = skill.category or "Other"
        categories.setdefault(cat, []).append(skill.name)

    parts = ["## Skills\n"]
    for category, names in categories.items():
        parts.append(f"### {category}")
        for name in names:
            parts.append(f"- {name}")
        parts.append("")  # blank line after category

    return "\n".join(parts).rstrip()
