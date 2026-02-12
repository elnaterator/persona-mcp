"""Pydantic models for persona resume data."""

from pydantic import BaseModel, field_validator


class ContactInfo(BaseModel):
    """Personal contact details stored in YAML front-matter."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    website: str | None = None
    github: str | None = None


class WorkExperience(BaseModel):
    """A single work experience entry."""

    title: str
    company: str
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    highlights: list[str] = []


class Education(BaseModel):
    """A single education entry."""

    institution: str
    degree: str
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    honors: str | None = None


class Skill(BaseModel):
    """A named skill with optional category."""

    name: str
    category: str | None = "Other"

    @field_validator("category", mode="before")
    @classmethod
    def default_empty_category(cls, v: str | None) -> str:
        if not v:
            return "Other"
        return v


class Resume(BaseModel):
    """Aggregate resume model combining all sections."""

    contact: ContactInfo = ContactInfo()
    summary: str = ""
    experience: list[WorkExperience] = []
    education: list[Education] = []
    skills: list[Skill] = []
