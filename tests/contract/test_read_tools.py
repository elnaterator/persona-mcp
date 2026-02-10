"""Contract tests for persona read tools (get_resume, get_resume_section)."""

from pathlib import Path

import pytest


class TestGetResume:
    """Contract tests for the get_resume MCP tool."""

    def test_returns_full_resume_from_valid_file(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(data_dir=tmp_data_dir)

        assert result["contact"]["name"] == "Jane Doe"
        assert result["contact"]["email"] == "jane@example.com"
        assert "Experienced software engineer" in result["summary"]
        assert len(result["experience"]) == 2
        assert result["experience"][0]["title"] == "Senior Software Engineer"
        assert len(result["education"]) == 2
        assert len(result["skills"]) >= 8

    def test_returns_empty_resume_when_file_absent(self, tmp_data_dir: Path) -> None:
        from persona.tools.read import get_resume

        result = get_resume(data_dir=tmp_data_dir)

        assert result["contact"]["name"] is None
        assert result["summary"] == ""
        assert result["experience"] == []
        assert result["education"] == []
        assert result["skills"] == []

    def test_returns_empty_resume_when_file_empty(
        self, empty_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(data_dir=tmp_data_dir)

        assert result["summary"] == ""
        assert result["experience"] == []

    def test_handles_malformed_file_gracefully(self, tmp_data_dir: Path) -> None:
        from persona.tools.read import get_resume

        resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
        resume_path.write_text("---\ninvalid: yaml: [broken\n---\n## Summary\nHello")

        result = get_resume(data_dir=tmp_data_dir)

        # Should not raise; returns empty/default data
        assert isinstance(result, dict)
        assert "contact" in result


class TestGetResumeSection:
    """Contract tests for the get_resume_section MCP tool."""

    def test_returns_contact_info(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="contact", data_dir=tmp_data_dir)

        assert result["name"] == "Jane Doe"
        assert result["email"] == "jane@example.com"
        assert result["phone"] == "+1-555-0100"

    def test_returns_summary(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="summary", data_dir=tmp_data_dir)

        assert isinstance(result, str)
        assert "Experienced software engineer" in result

    def test_returns_experience_list(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="experience", data_dir=tmp_data_dir)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Senior Software Engineer"
        assert result[0]["company"] == "Acme Corp"

    def test_returns_education_list(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="education", data_dir=tmp_data_dir)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["institution"] == "Stanford University"

    def test_returns_skills_list(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section

        result = get_resume_section(section="skills", data_dir=tmp_data_dir)

        assert isinstance(result, list)
        assert len(result) >= 8
        python_skills = [s for s in result if s["name"] == "Python"]
        assert len(python_skills) == 1

    def test_error_on_invalid_section(self, tmp_data_dir: Path) -> None:
        from persona.tools.read import get_resume_section

        with pytest.raises(ValueError, match="Invalid section"):
            get_resume_section(section="invalid", data_dir=tmp_data_dir)
