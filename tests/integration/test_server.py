"""Integration tests for persona MCP server — end-to-end tool invocation."""

import json
import time
from pathlib import Path


def _make_large_resume(num_entries: int = 50) -> str:
    """Generate a resume.md with many entries for performance testing."""
    lines = [
        "---",
        'name: "Perf Test User"',
        'email: "perf@test.com"',
        "---",
        "",
        "## Summary",
        "",
        "A performance test resume.",
        "",
        "## Experience",
        "",
    ]
    for i in range(num_entries):
        lines.extend(
            [
                f"### Engineer {i} | Company {i}",
                f"- **Start**: 20{i % 25:02d}-01",
                f"- **End**: 20{(i % 25) + 1:02d}-01",
                f"- **Location**: City {i}",
                "",
                f"- Built feature {i}",
                "",
            ]
        )

    lines.extend(["## Education", ""])
    for i in range(5):
        lines.extend(
            [
                f"### Degree {i} | University {i}",
                f"- **Start**: 20{i:02d}-09",
                f"- **End**: 20{i + 4:02d}-05",
                "",
            ]
        )

    lines.extend(["## Skills", "", "### Languages"])
    for i in range(10):
        lines.append(f"- Skill{i}")

    return "\n".join(lines) + "\n"


class TestServerReadTools:
    """Integration tests for read tools via direct function calls."""

    def test_get_resume_returns_full_data(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(data_dir=tmp_data_dir)

        assert result["contact"]["name"] == "Jane Doe"
        assert len(result["experience"]) == 2
        assert len(result["education"]) == 2
        assert len(result["skills"]) >= 8
        assert "Experienced software engineer" in result["summary"]

    def test_get_resume_section_contact(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section

        contact = get_resume_section(section="contact", data_dir=tmp_data_dir)

        assert contact["name"] == "Jane Doe"
        assert contact["email"] == "jane@example.com"

    def test_get_resume_section_experience(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section

        experience = get_resume_section(section="experience", data_dir=tmp_data_dir)

        assert len(experience) == 2
        assert experience[0]["title"] == "Senior Software Engineer"
        assert experience[0]["company"] == "Acme Corp"
        assert experience[0]["highlights"] == [
            "Led migration of monolithic application to microservices",
            "Reduced deployment time by 60%",
        ]

    def test_result_is_json_serializable(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume

        result = get_resume(data_dir=tmp_data_dir)

        # Must be JSON-serializable for MCP transport
        serialized = json.dumps(result)
        assert isinstance(serialized, str)

    def test_performance_under_2s_with_large_resume(self, tmp_data_dir: Path) -> None:
        """SC-001: Read operations complete in under 2 seconds with 50 entries."""
        from persona.tools.read import get_resume

        resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
        resume_path.write_text(_make_large_resume(50))

        start = time.monotonic()
        result = get_resume(data_dir=tmp_data_dir)
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, f"get_resume took {elapsed:.2f}s, expected <2s"
        assert len(result["experience"]) == 50


class TestServerWriteTools:
    """Integration tests for write tools — add, read back, update, remove."""

    def test_add_read_update_remove_experience(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry, remove_entry, update_entry

        # Add
        add_entry(
            section="experience",
            data={
                "title": "VP Engineering",
                "company": "BigCo",
                "start_date": "2024-01",
            },
            data_dir=tmp_data_dir,
        )
        experience = get_resume_section(section="experience", data_dir=tmp_data_dir)
        assert len(experience) == 3
        assert experience[0]["title"] == "VP Engineering"

        # Update
        update_entry(
            section="experience",
            index=0,
            data={"title": "SVP Engineering"},
            data_dir=tmp_data_dir,
        )
        experience = get_resume_section(section="experience", data_dir=tmp_data_dir)
        assert experience[0]["title"] == "SVP Engineering"

        # Remove
        remove_entry(section="experience", index=0, data_dir=tmp_data_dir)
        experience = get_resume_section(section="experience", data_dir=tmp_data_dir)
        assert len(experience) == 2

    def test_update_contact_and_summary(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_section

        # Update contact
        update_section(
            section="contact",
            data={"name": "Jane Smith", "email": "smith@new.com"},
            data_dir=tmp_data_dir,
        )
        contact = get_resume_section(section="contact", data_dir=tmp_data_dir)
        assert contact["name"] == "Jane Smith"
        assert contact["email"] == "smith@new.com"
        # Phone preserved
        assert contact["phone"] == "+1-555-0100"

        # Update summary
        update_section(
            section="summary",
            data={"text": "Updated summary."},
            data_dir=tmp_data_dir,
        )
        summary = get_resume_section(section="summary", data_dir=tmp_data_dir)
        assert summary == "Updated summary."

    def test_write_results_are_json_serializable(
        self, sample_resume_path: Path, tmp_data_dir: Path
    ) -> None:
        from persona.tools.write import add_entry

        result = add_entry(
            section="skills",
            data={"name": "NewLang", "category": "Languages"},
            data_dir=tmp_data_dir,
        )
        serialized = json.dumps(result)
        assert isinstance(serialized, str)
