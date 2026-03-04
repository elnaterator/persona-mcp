"""Unit tests for persona.models module."""

import pytest
from pydantic import ValidationError


class TestContactInfo:
    """Tests for ContactInfo model — all fields optional."""

    def test_empty_contact_info(self) -> None:
        from persona.models import ContactInfo

        contact = ContactInfo()
        assert contact.name is None
        assert contact.email is None
        assert contact.phone is None
        assert contact.location is None
        assert contact.linkedin is None
        assert contact.website is None
        assert contact.github is None

    def test_full_contact_info(self) -> None:
        from persona.models import ContactInfo

        contact = ContactInfo(
            name="Jane Doe",
            email="jane@example.com",
            phone="+1-555-0100",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/janedoe",
            website="https://janedoe.dev",
            github="https://github.com/janedoe",
        )
        assert contact.name == "Jane Doe"
        assert contact.email == "jane@example.com"

    def test_partial_contact_info(self) -> None:
        from persona.models import ContactInfo

        contact = ContactInfo(name="Jane", email="jane@example.com")
        assert contact.name == "Jane"
        assert contact.phone is None


class TestWorkExperience:
    """Tests for WorkExperience model — title and company required."""

    def test_valid_experience(self) -> None:
        from persona.models import WorkExperience

        exp = WorkExperience(
            title="Software Engineer",
            company="Acme Corp",
            start_date="2021-01",
            end_date="present",
            location="SF, CA",
            highlights=["Built things"],
        )
        assert exp.title == "Software Engineer"
        assert exp.company == "Acme Corp"

    def test_minimal_experience(self) -> None:
        from persona.models import WorkExperience

        exp = WorkExperience(title="Engineer", company="Co")
        assert exp.start_date is None
        assert exp.highlights == []

    def test_missing_title_raises(self) -> None:
        from persona.models import WorkExperience

        with pytest.raises(ValidationError):
            WorkExperience(company="Acme Corp")  # type: ignore[call-arg]

    def test_missing_company_raises(self) -> None:
        from persona.models import WorkExperience

        with pytest.raises(ValidationError):
            WorkExperience(title="Engineer")  # type: ignore[call-arg]


class TestEducation:
    """Tests for Education model — institution and degree required."""

    def test_valid_education(self) -> None:
        from persona.models import Education

        edu = Education(
            institution="Stanford University",
            degree="M.S. Computer Science",
            field="Computer Science",
            start_date="2016-09",
            end_date="2018-05",
            honors="Dean's List",
        )
        assert edu.institution == "Stanford University"
        assert edu.degree == "M.S. Computer Science"

    def test_minimal_education(self) -> None:
        from persona.models import Education

        edu = Education(institution="MIT", degree="B.S.")
        assert edu.field is None
        assert edu.honors is None

    def test_missing_institution_raises(self) -> None:
        from persona.models import Education

        with pytest.raises(ValidationError):
            Education(degree="B.S.")  # type: ignore[call-arg]

    def test_missing_degree_raises(self) -> None:
        from persona.models import Education

        with pytest.raises(ValidationError):
            Education(institution="MIT")  # type: ignore[call-arg]

    def test_highlights_defaults_to_empty_list(self) -> None:
        from persona.models import Education

        edu = Education(institution="MIT", degree="B.S.")
        assert edu.highlights == []

    def test_highlights_with_values(self) -> None:
        from persona.models import Education

        edu = Education(
            institution="UC Berkeley",
            degree="B.S. CS",
            highlights=["Dean's List", "Thesis on X"],
        )
        assert edu.highlights == ["Dean's List", "Thesis on X"]

    def test_highlights_preserved_in_serialization(self) -> None:
        from persona.models import Education

        edu = Education(
            institution="MIT",
            degree="B.S.",
            highlights=["Dean's List", "Graduated with Honors"],
        )
        data = edu.model_dump()
        assert data["highlights"] == ["Dean's List", "Graduated with Honors"]


class TestSkill:
    """Tests for Skill model — name required, category defaults to 'Other'."""

    def test_skill_with_category(self) -> None:
        from persona.models import Skill

        skill = Skill(name="Python", category="Programming Languages")
        assert skill.name == "Python"
        assert skill.category == "Programming Languages"

    def test_skill_defaults_category_to_other(self) -> None:
        from persona.models import Skill

        skill = Skill(name="Python")
        assert skill.category == "Other"

    def test_missing_name_raises(self) -> None:
        from persona.models import Skill

        with pytest.raises(ValidationError):
            Skill()  # type: ignore[call-arg]

    def test_empty_category_defaults_to_other(self) -> None:
        from persona.models import Skill

        skill = Skill(name="Python", category="")
        assert skill.category == "Other"

    def test_none_category_defaults_to_other(self) -> None:
        from persona.models import Skill

        skill = Skill(name="Python", category=None)
        assert skill.category == "Other"


class TestResume:
    """Tests for Resume aggregate model with empty defaults."""

    def test_empty_resume(self) -> None:
        from persona.models import Resume

        resume = Resume()
        assert resume.contact.name is None
        assert resume.summary == ""
        assert resume.experience == []
        assert resume.education == []
        assert resume.skills == []

    def test_resume_with_data(self) -> None:
        from persona.models import ContactInfo, Education, Resume, Skill, WorkExperience

        resume = Resume(
            contact=ContactInfo(name="Jane"),
            summary="A summary",
            experience=[WorkExperience(title="Eng", company="Co")],
            education=[Education(institution="MIT", degree="BS")],
            skills=[Skill(name="Python")],
        )
        assert resume.contact.name == "Jane"
        assert len(resume.experience) == 1
        assert len(resume.education) == 1
        assert len(resume.skills) == 1
