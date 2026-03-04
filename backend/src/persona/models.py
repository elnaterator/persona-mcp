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
    highlights: list[str] = []


class Skill(BaseModel):
    """A single skill with a name and optional category."""

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


class ResumeVersion(BaseModel):
    """A versioned resume with metadata."""

    id: int
    label: str
    is_default: bool = False
    resume_data: Resume = Resume()
    created_at: str = ""
    updated_at: str = ""


class ResumeVersionSummary(BaseModel):
    """Resume version metadata for list views (no resume_data)."""

    id: int
    label: str
    is_default: bool = False
    app_count: int = 0
    created_at: str = ""
    updated_at: str = ""


APPLICATION_STATUSES = (
    "Interested",
    "Applied",
    "Phone Screen",
    "Interview",
    "Offer",
    "Accepted",
    "Rejected",
    "Withdrawn",
)

COMMUNICATION_TYPES = ("email", "phone", "interview_note", "other")
COMMUNICATION_DIRECTIONS = ("sent", "received")
COMMUNICATION_STATUSES = ("draft", "ready", "sent", "archived")


class Application(BaseModel):
    """A job application."""

    id: int
    company: str
    position: str
    description: str = ""
    status: str = "Interested"
    url: str | None = None
    notes: str = ""
    resume_version_id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in APPLICATION_STATUSES:
            valid = ", ".join(APPLICATION_STATUSES)
            raise ValueError(f"Invalid status: '{v}'. Must be one of: {valid}")
        return v


class ApplicationSummary(BaseModel):
    """Application summary for list views (no description/notes)."""

    id: int
    company: str
    position: str
    status: str = "Interested"
    url: str | None = None
    resume_version_id: int | None = None
    created_at: str = ""
    updated_at: str = ""


class ApplicationContact(BaseModel):
    """A contact associated with a job application."""

    id: int
    app_id: int
    name: str
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str = ""


class Accomplishment(BaseModel):
    """A career accomplishment in STAR format."""

    id: int
    title: str
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    accomplishment_date: str | None = None
    tags: list[str] = []
    created_at: str = ""
    updated_at: str = ""


class AccomplishmentSummary(BaseModel):
    """Accomplishment summary for list views (STAR body omitted)."""

    id: int
    title: str
    accomplishment_date: str | None = None
    tags: list[str] = []
    created_at: str = ""
    updated_at: str = ""


class Communication(BaseModel):
    """A communication entry for a job application."""

    id: int
    app_id: int
    contact_id: int | None = None
    contact_name: str | None = None
    type: str
    direction: str
    subject: str = ""
    body: str
    date: str
    status: str = "sent"
    created_at: str = ""

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in COMMUNICATION_TYPES:
            raise ValueError(
                f"Invalid type: '{v}'. Must be one of: {', '.join(COMMUNICATION_TYPES)}"
            )
        return v

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in COMMUNICATION_DIRECTIONS:
            valid = ", ".join(COMMUNICATION_DIRECTIONS)
            raise ValueError(f"Invalid direction: '{v}'. Must be one of: {valid}")
        return v

    @field_validator("status")
    @classmethod
    def validate_comm_status(cls, v: str) -> str:
        if v not in COMMUNICATION_STATUSES:
            valid = ", ".join(COMMUNICATION_STATUSES)
            raise ValueError(f"Invalid status: '{v}'. Must be one of: {valid}")
        return v
