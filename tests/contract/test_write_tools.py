"""Contract tests for persona write tools (update_section, add/update/remove_entry)."""

import sqlite3

import pytest


class TestUpdateSection:
    """Contract tests for the update_section tool."""

    def test_update_contact_partial(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import update_section

        update_section(
            section="contact",
            data={"email": "new@example.com"},
            conn=db_conn_with_data,
        )

        contact = get_resume_section(section="contact", conn=db_conn_with_data)
        assert contact["email"] == "new@example.com"
        assert contact["name"] == "Jane Doe"
        assert contact["phone"] == "+1-555-0100"

    def test_update_summary(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import update_section

        update_section(
            section="summary",
            data={"text": "A brand new summary."},
            conn=db_conn_with_data,
        )

        summary = get_resume_section(section="summary", conn=db_conn_with_data)
        assert summary == "A brand new summary."

    def test_error_on_invalid_section(self, db_conn: sqlite3.Connection) -> None:
        from backend.tools.write import update_section

        with pytest.raises(ValueError, match="Invalid section"):
            update_section(
                section="experience",
                data={"title": "x"},
                conn=db_conn,
            )

    def test_error_on_empty_contact_update(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.write import update_section

        with pytest.raises(ValueError, match="At least one contact field"):
            update_section(section="contact", data={}, conn=db_conn_with_data)

    def test_error_on_empty_summary_text(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.write import update_section

        with pytest.raises(ValueError, match="Summary text must not be empty"):
            update_section(section="summary", data={"text": ""}, conn=db_conn_with_data)


class TestAddEntry:
    """Contract tests for the add_entry tool."""

    def test_add_experience_prepended(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import add_entry

        add_entry(
            section="experience",
            data={
                "title": "CTO",
                "company": "NewCo",
                "start_date": "2024-01",
                "end_date": "present",
                "location": "Remote",
                "highlights": ["Led company"],
            },
            conn=db_conn_with_data,
        )

        experience = get_resume_section(section="experience", conn=db_conn_with_data)
        assert len(experience) == 3
        assert experience[0]["title"] == "CTO"
        assert experience[0]["company"] == "NewCo"

    def test_add_education(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import add_entry

        add_entry(
            section="education",
            data={
                "institution": "New University",
                "degree": "Ph.D.",
                "start_date": "2020-09",
            },
            conn=db_conn_with_data,
        )

        education = get_resume_section(section="education", conn=db_conn_with_data)
        assert len(education) == 3
        assert education[0]["institution"] == "New University"

    def test_add_skill_with_category(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import add_entry

        add_entry(
            section="skills",
            data={"name": "Rust", "category": "Programming Languages"},
            conn=db_conn_with_data,
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)
        rust = [s for s in skills if s["name"] == "Rust"]
        assert len(rust) == 1
        assert rust[0]["category"] == "Programming Languages"

    def test_add_skill_default_category(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import add_entry

        add_entry(
            section="skills",
            data={"name": "NewSkill"},
            conn=db_conn_with_data,
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)
        new_skill = [s for s in skills if s["name"] == "NewSkill"]
        assert len(new_skill) == 1
        assert new_skill[0]["category"] == "Other"

    def test_error_on_missing_required_fields(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from backend.tools.write import add_entry

        with pytest.raises(ValueError, match="required"):
            add_entry(
                section="experience",
                data={"title": "Engineer"},  # missing company
                conn=db_conn,
            )

    def test_error_on_duplicate_skill(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.write import add_entry

        with pytest.raises(ValueError, match="already exists"):
            add_entry(
                section="skills",
                data={"name": "Python"},
                conn=db_conn_with_data,
            )

    def test_error_on_invalid_section(self, db_conn: sqlite3.Connection) -> None:
        from backend.tools.write import add_entry

        with pytest.raises(ValueError, match="Invalid section"):
            add_entry(section="contact", data={"name": "x"}, conn=db_conn)


class TestUpdateEntry:
    """Contract tests for the update_entry tool."""

    def test_update_experience_by_index(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import update_entry

        update_entry(
            section="experience",
            index=0,
            data={"title": "Staff Engineer"},
            conn=db_conn_with_data,
        )

        experience = get_resume_section(section="experience", conn=db_conn_with_data)
        assert experience[0]["title"] == "Staff Engineer"
        assert experience[0]["company"] == "Acme Corp"

    def test_update_education_by_index(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import update_entry

        update_entry(
            section="education",
            index=1,
            data={"honors": "Summa Cum Laude"},
            conn=db_conn_with_data,
        )

        education = get_resume_section(section="education", conn=db_conn_with_data)
        assert education[1]["honors"] == "Summa Cum Laude"

    def test_update_skill_by_index(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import update_entry

        update_entry(
            section="skills",
            index=0,
            data={"name": "Python 3"},
            conn=db_conn_with_data,
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)
        assert skills[0]["name"] == "Python 3"

    def test_error_on_out_of_range_index(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.write import update_entry

        with pytest.raises(ValueError, match="out of range"):
            update_entry(
                section="experience",
                index=99,
                data={"title": "x"},
                conn=db_conn_with_data,
            )

    def test_error_on_empty_data(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.write import update_entry

        with pytest.raises(ValueError, match="At least one field"):
            update_entry(
                section="experience",
                index=0,
                data={},
                conn=db_conn_with_data,
            )


class TestRemoveEntry:
    """Contract tests for the remove_entry tool."""

    def test_remove_experience_by_index(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import remove_entry

        remove_entry(section="experience", index=0, conn=db_conn_with_data)

        experience = get_resume_section(section="experience", conn=db_conn_with_data)
        assert len(experience) == 1
        assert experience[0]["title"] == "Software Engineer"

    def test_remove_education_by_index(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import remove_entry

        remove_entry(section="education", index=1, conn=db_conn_with_data)

        education = get_resume_section(section="education", conn=db_conn_with_data)
        assert len(education) == 1
        assert education[0]["institution"] == "Stanford University"

    def test_remove_skill_by_index(self, db_conn_with_data: sqlite3.Connection) -> None:
        from backend.tools.read import get_resume_section
        from backend.tools.write import remove_entry

        skills_before = get_resume_section(section="skills", conn=db_conn_with_data)
        count_before = len(skills_before)
        first_name = skills_before[0]["name"]

        remove_entry(section="skills", index=0, conn=db_conn_with_data)

        skills_after = get_resume_section(section="skills", conn=db_conn_with_data)
        assert len(skills_after) == count_before - 1
        assert skills_after[0]["name"] != first_name

    def test_error_on_out_of_range_index(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from backend.tools.write import remove_entry

        with pytest.raises(ValueError, match="out of range"):
            remove_entry(section="experience", index=99, conn=db_conn_with_data)

    def test_error_on_invalid_section(self, db_conn: sqlite3.Connection) -> None:
        from backend.tools.write import remove_entry

        with pytest.raises(ValueError, match="Invalid section"):
            remove_entry(section="contact", index=0, conn=db_conn)
