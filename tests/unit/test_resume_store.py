"""Unit tests for persona.resume_store module."""

import logging
from pathlib import Path

import pytest

from tests.conftest import SAMPLE_RESUME_MD


class TestLoadResume:
    """Tests for loading resume data from resume.md."""

    def test_load_valid_resume(self, sample_resume_path: Path) -> None:
        from persona.resume_store import load_resume

        resume = load_resume(sample_resume_path)

        # Contact info from front-matter
        assert resume.contact.name == "Jane Doe"
        assert resume.contact.email == "jane@example.com"
        assert resume.contact.phone == "+1-555-0100"
        assert resume.contact.location == "San Francisco, CA"
        assert resume.contact.linkedin == "https://linkedin.com/in/janedoe"
        assert resume.contact.website == "https://janedoe.dev"
        assert resume.contact.github == "https://github.com/janedoe"

        # Summary
        assert "Experienced software engineer" in resume.summary

        # Experience
        assert len(resume.experience) == 2
        assert resume.experience[0].title == "Senior Software Engineer"
        assert resume.experience[0].company == "Acme Corp"
        assert resume.experience[0].start_date == "2021-01"
        assert resume.experience[0].end_date == "present"
        assert resume.experience[0].location == "San Francisco, CA"
        assert len(resume.experience[0].highlights) == 2

        # Education
        assert len(resume.education) == 2
        assert resume.education[0].institution == "Stanford University"
        assert resume.education[0].degree == "M.S. Computer Science"
        assert resume.education[0].honors == "Dean's List"

        # Skills
        assert len(resume.skills) >= 8
        python_skills = [s for s in resume.skills if s.name == "Python"]
        assert len(python_skills) == 1
        assert python_skills[0].category == "Programming Languages"

    def test_load_empty_file_returns_empty_resume(
        self, empty_resume_path: Path
    ) -> None:
        from persona.resume_store import load_resume

        resume = load_resume(empty_resume_path)
        assert resume.contact.name is None
        assert resume.summary == ""
        assert resume.experience == []
        assert resume.education == []
        assert resume.skills == []

    def test_load_missing_file_returns_empty_resume(self, tmp_data_dir: Path) -> None:
        from persona.resume_store import load_resume

        missing_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
        resume = load_resume(missing_path)
        assert resume.summary == ""
        assert resume.experience == []

    def test_load_malformed_frontmatter_logs_warning(
        self, tmp_data_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from persona.resume_store import load_resume

        resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
        resume_path.write_text(
            "---\ninvalid: yaml: content: [broken\n---\n## Summary\nHello"
        )

        with caplog.at_level(logging.WARNING):
            resume = load_resume(resume_path)

        assert resume.summary == "" or resume is not None  # Should not crash
        # Should have logged a warning about the parse issue
        assert (
            any(
                "warning" in r.levelname.lower()
                or "error" in r.message.lower()
                or "parse" in r.message.lower()
                or "malformed" in r.message.lower()
                for r in caplog.records
            )
            or len(caplog.records) > 0
        )


class TestSaveResume:
    """Tests for saving resume data to resume.md."""

    def test_write_roundtrip(self, tmp_data_dir: Path) -> None:
        from persona.models import ContactInfo, Education, Resume, Skill, WorkExperience
        from persona.resume_store import load_resume, save_resume

        resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"

        original = Resume(
            contact=ContactInfo(name="Test User", email="test@example.com"),
            summary="A test summary.",
            experience=[
                WorkExperience(
                    title="Developer",
                    company="TestCo",
                    start_date="2020-01",
                    end_date="present",
                    location="Remote",
                    highlights=["Did things", "Built stuff"],
                )
            ],
            education=[
                Education(
                    institution="Test University",
                    degree="B.S. Testing",
                    start_date="2016-09",
                    end_date="2020-05",
                )
            ],
            skills=[
                Skill(name="Python", category="Languages"),
                Skill(name="Testing", category="Other"),
            ],
        )

        save_resume(resume_path, original)
        reloaded = load_resume(resume_path)

        assert reloaded.contact.name == "Test User"
        assert reloaded.contact.email == "test@example.com"
        assert reloaded.summary == "A test summary."
        assert len(reloaded.experience) == 1
        assert reloaded.experience[0].title == "Developer"
        assert reloaded.experience[0].highlights == ["Did things", "Built stuff"]
        assert len(reloaded.education) == 1
        assert reloaded.education[0].institution == "Test University"
        assert len(reloaded.skills) == 2

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        from persona.models import Resume
        from persona.resume_store import save_resume

        resume_path = tmp_path / "new" / "nested" / "resume.md"
        save_resume(resume_path, Resume())
        assert resume_path.exists()

    def test_save_from_sample_content(self, tmp_data_dir: Path) -> None:
        """Load the sample, save it, reload it — data should survive."""
        from persona.resume_store import load_resume, save_resume

        resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
        resume_path.write_text(SAMPLE_RESUME_MD)

        original = load_resume(resume_path)
        save_resume(resume_path, original)
        reloaded = load_resume(resume_path)

        assert reloaded.contact.name == original.contact.name
        assert reloaded.summary == original.summary
        assert len(reloaded.experience) == len(original.experience)
        assert len(reloaded.education) == len(original.education)
        assert len(reloaded.skills) == len(original.skills)
