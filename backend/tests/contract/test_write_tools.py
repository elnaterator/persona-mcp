"""Contract tests for persona write tools (update_section, add/update/remove_entry)."""

from typing import Any

import pytest
from psycopg import Connection


class TestUpdateSection:
    """Contract tests for the update_section tool."""

    def test_update_contact_partial(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_section

        update_section(
            section="contact",
            data={"email": "new@example.com"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        contact = get_resume_section(section="contact", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert contact["email"] == "new@example.com"
        assert contact["name"] == "Jane Doe"
        assert contact["phone"] == "+1-555-0100"

    def test_update_summary(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_section

        update_section(
            section="summary",
            data={"text": "A brand new summary."},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        summary = get_resume_section(section="summary", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert summary == "A brand new summary."

    def test_error_on_invalid_section(self, db_conn: Connection[Any]) -> None:
        from persona.tools.write import update_section

        with pytest.raises(ValueError, match="Invalid section"):
            update_section(
                section="experience",
                data={"title": "x"},
                conn=db_conn,  # type: ignore[arg-type]
            )

    def test_error_on_empty_contact_update(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.write import update_section

        with pytest.raises(ValueError, match="At least one contact field"):
            update_section(section="contact", data={}, conn=db_conn_with_data)  # type: ignore[arg-type]

    def test_error_on_empty_summary_text(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.write import update_section

        with pytest.raises(ValueError, match="Summary text must not be empty"):
            update_section(section="summary", data={"text": ""}, conn=db_conn_with_data)  # type: ignore[arg-type]


class TestAddEntry:
    """Contract tests for the add_entry tool."""

    def test_add_experience_prepended(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry

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
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        experience = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert len(experience) == 3
        assert experience[0]["title"] == "CTO"
        assert experience[0]["company"] == "NewCo"

    def test_add_education(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry

        add_entry(
            section="education",
            data={
                "institution": "New University",
                "degree": "Ph.D.",
                "start_date": "2020-09",
            },
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        education = get_resume_section(section="education", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert len(education) == 3
        assert education[0]["institution"] == "New University"

    def test_add_skill_with_category(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry

        add_entry(
            section="skills",
            data={"name": "Rust", "category": "Programming Languages"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]
        rust = [s for s in skills if s["name"] == "Rust"]
        assert len(rust) == 1
        assert rust[0]["category"] == "Programming Languages"

    def test_add_skill_with_items(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry

        add_entry(
            section="skills",
            data={"name": "Languages", "items": ["Python", "TypeScript", "Go"]},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]
        langs = [s for s in skills if s["name"] == "Languages"]
        assert len(langs) == 1
        assert langs[0]["items"] == ["Python", "TypeScript", "Go"]

    def test_add_skill_items_default_to_empty_list(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry

        add_entry(
            section="skills",
            data={"name": "Rust", "category": "Systems"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]
        rust = [s for s in skills if s["name"] == "Rust"]
        assert rust[0]["items"] == []

    def test_add_skill_default_category(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import add_entry

        add_entry(
            section="skills",
            data={"name": "NewSkill"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]
        new_skill = [s for s in skills if s["name"] == "NewSkill"]
        assert len(new_skill) == 1
        assert new_skill[0]["category"] == "Other"

    def test_error_on_missing_required_fields(self, db_conn: Connection[Any]) -> None:
        from persona.tools.write import add_entry

        with pytest.raises(ValueError, match="required"):
            add_entry(
                section="experience",
                data={"title": "Engineer"},  # missing company
                conn=db_conn,  # type: ignore[arg-type]
            )

    def test_error_on_duplicate_skill(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.write import add_entry

        with pytest.raises(ValueError, match="already exists"):
            add_entry(
                section="skills",
                data={"name": "Python"},
                conn=db_conn_with_data,  # type: ignore[arg-type]
            )

    def test_error_on_invalid_section(self, db_conn: Connection[Any]) -> None:
        from persona.tools.write import add_entry

        with pytest.raises(ValueError, match="Invalid section"):
            add_entry(section="contact", data={"name": "x"}, conn=db_conn)  # type: ignore[arg-type]


class TestUpdateEntry:
    """Contract tests for the update_entry tool."""

    def test_update_experience_by_index(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_entry

        update_entry(
            section="experience",
            index=0,
            data={"title": "Staff Engineer"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        experience = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert experience[0]["title"] == "Staff Engineer"
        assert experience[0]["company"] == "Acme Corp"

    def test_update_education_by_index(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_entry

        update_entry(
            section="education",
            index=1,
            data={"honors": "Summa Cum Laude"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        education = get_resume_section(section="education", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert education[1]["honors"] == "Summa Cum Laude"

    def test_update_skill_by_index(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import update_entry

        update_entry(
            section="skills",
            index=0,
            data={"name": "Python 3"},
            conn=db_conn_with_data,  # type: ignore[arg-type]
        )

        skills = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert skills[0]["name"] == "Python 3"

    def test_error_on_out_of_range_index(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.write import update_entry

        with pytest.raises(ValueError, match="out of range"):
            update_entry(
                section="experience",
                index=99,
                data={"title": "x"},
                conn=db_conn_with_data,  # type: ignore[arg-type]
            )

    def test_error_on_empty_data(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.write import update_entry

        with pytest.raises(ValueError, match="At least one field"):
            update_entry(
                section="experience",
                index=0,
                data={},
                conn=db_conn_with_data,  # type: ignore[arg-type]
            )


class TestRemoveEntry:
    """Contract tests for the remove_entry tool."""

    def test_remove_experience_by_index(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import remove_entry

        remove_entry(section="experience", index=0, conn=db_conn_with_data)  # type: ignore[arg-type]

        experience = get_resume_section(section="experience", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert len(experience) == 1
        assert experience[0]["title"] == "Software Engineer"

    def test_remove_education_by_index(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import remove_entry

        remove_entry(section="education", index=1, conn=db_conn_with_data)  # type: ignore[arg-type]

        education = get_resume_section(section="education", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert len(education) == 1
        assert education[0]["institution"] == "Stanford University"

    def test_remove_skill_by_index(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.tools.read import get_resume_section
        from persona.tools.write import remove_entry

        skills_before = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]
        count_before = len(skills_before)
        first_name = skills_before[0]["name"]

        remove_entry(section="skills", index=0, conn=db_conn_with_data)  # type: ignore[arg-type]

        skills_after = get_resume_section(section="skills", conn=db_conn_with_data)  # type: ignore[arg-type]
        assert len(skills_after) == count_before - 1
        assert skills_after[0]["name"] != first_name

    def test_error_on_out_of_range_index(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.tools.write import remove_entry

        with pytest.raises(ValueError, match="out of range"):
            remove_entry(section="experience", index=99, conn=db_conn_with_data)  # type: ignore[arg-type]

    def test_error_on_invalid_section(self, db_conn: Connection[Any]) -> None:
        from persona.tools.write import remove_entry

        with pytest.raises(ValueError, match="Invalid section"):
            remove_entry(section="contact", index=0, conn=db_conn)  # type: ignore[arg-type]


class TestResumeVersionWriteTools:
    """Contract tests for resume version MCP write tools."""

    def test_create_resume_returns_message(self, db_conn: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)  # type: ignore[arg-type]
        result = service.create_resume("My Resume")

        assert result["label"] == "My Resume"
        assert result["is_default"] is False

    def test_set_default_resume(self, db_conn: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)  # type: ignore[arg-type]
        new_version = service.create_resume("New Default")
        msg = service.set_default(new_version["id"])

        assert isinstance(msg, str)
        default = service.get_resume()
        assert default["id"] == new_version["id"]

    def test_delete_resume_removes_version(self, db_conn: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)  # type: ignore[arg-type]
        v2 = service.create_resume("Temp")
        service.delete_resume(v2["id"])

        versions = service.list_resumes()
        ids = [v["id"] for v in versions]
        assert v2["id"] not in ids

    def test_delete_last_resume_raises(self, db_conn: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)  # type: ignore[arg-type]
        default = service.get_resume()
        with pytest.raises(ValueError, match="last remaining"):
            service.delete_resume(default["id"])

    def test_update_resume_section_contact(
        self, db_conn_with_data: Connection[Any]
    ) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        default = service.get_resume()
        msg = service.update_section(
            "contact", {"email": "new@example.com"}, default["id"]
        )

        assert isinstance(msg, str)
        contact = service.get_section("contact", version_id=default["id"])
        assert contact["email"] == "new@example.com"
        assert contact["name"] == "Jane Doe"

    def test_add_resume_entry(self, db_conn: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn)  # type: ignore[arg-type]
        default = service.get_resume()
        msg = service.add_entry(
            "experience", {"title": "Dev", "company": "Corp"}, default["id"]
        )

        assert isinstance(msg, str)
        experience = service.get_section("experience", version_id=default["id"])
        assert len(experience) == 1

    def test_update_resume_entry(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        default = service.get_resume()
        msg = service.update_entry(
            "experience", 0, {"title": "Staff Engineer"}, default["id"]
        )

        assert isinstance(msg, str)
        experience = service.get_section("experience", version_id=default["id"])
        assert experience[0]["title"] == "Staff Engineer"

    def test_remove_resume_entry(self, db_conn_with_data: Connection[Any]) -> None:
        from persona.resume_service import ResumeService

        service = ResumeService(db_conn_with_data)  # type: ignore[arg-type]
        default = service.get_resume()
        initial_count = len(service.get_section("experience", version_id=default["id"]))
        msg = service.remove_entry("experience", 0, default["id"])

        assert isinstance(msg, str)
        experience = service.get_section("experience", version_id=default["id"])
        assert len(experience) == initial_count - 1


class TestApplicationTools:
    """Contract tests for application MCP write tools."""

    def test_create_application(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Acme", "position": "Engineer"})

        assert app["company"] == "Acme"
        assert app["position"] == "Engineer"
        assert app["status"] == "Interested"

    def test_update_application(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        updated = svc.update_application(
            app["id"], {"status": "Applied", "notes": "Good"}
        )

        assert updated["status"] == "Applied"
        assert updated["notes"] == "Good"

    def test_delete_application_returns_data(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        deleted = svc.delete_application(app["id"])

        assert deleted["company"] == "Corp"
        with pytest.raises(ValueError, match="not found"):
            svc.get_application(app["id"])

    def test_create_application_invalid_status_raises(
        self, db_conn: Connection[Any]
    ) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Invalid status"):
            svc.create_application(
                {"company": "Corp", "position": "Dev", "status": "NotValid"}
            )


class TestContactTools:
    """Contract tests for contact MCP write tools."""

    def test_add_contact(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        contact = svc.add_contact(
            app["id"], {"name": "Alice", "email": "alice@corp.com"}
        )

        assert contact["name"] == "Alice"
        assert contact["email"] == "alice@corp.com"
        assert contact["app_id"] == app["id"]

    def test_update_contact(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        contact = svc.add_contact(app["id"], {"name": "Bob"})
        updated = svc.update_contact(contact["id"], {"role": "HR"})

        assert updated["role"] == "HR"
        assert updated["name"] == "Bob"

    def test_remove_contact(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        contact = svc.add_contact(app["id"], {"name": "Alice"})
        name = svc.remove_contact(contact["id"])

        assert name == "Alice"
        contacts = svc.list_contacts(app["id"])
        assert len(contacts) == 0

    def test_remove_contact_not_found_raises(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="not found"):
            svc.remove_contact(9999)


class TestCommunicationTools:
    """Contract tests for communication MCP write tools."""

    def test_add_communication(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        comm = svc.add_communication(
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Applying for the role.",
                "date": "2024-01-15",
                "subject": "Application",
                "status": "draft",
            },
        )

        assert comm["type"] == "email"
        assert comm["direction"] == "sent"
        assert comm["subject"] == "Application"
        assert comm["status"] == "draft"

    def test_update_communication(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        comm = svc.add_communication(
            app["id"],
            {"type": "email", "direction": "sent", "body": "Hi", "date": "2024-01-01"},
        )
        updated = svc.update_communication(comm["id"], {"body": "Updated body"})

        assert updated["body"] == "Updated body"

    def test_remove_communication(self, db_conn: Connection[Any]) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        app = svc.create_application({"company": "Corp", "position": "Dev"})
        comm = svc.add_communication(
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Hello",
                "date": "2024-01-01",
                "subject": "Greetings",
            },
        )
        subject = svc.remove_communication(comm["id"])

        assert subject == "Greetings"
        comms = svc.list_communications(app["id"])
        assert len(comms) == 0

    def test_remove_communication_not_found_raises(
        self, db_conn: Connection[Any]
    ) -> None:
        from persona.application_service import ApplicationService

        svc = ApplicationService(db_conn)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="not found"):
            svc.remove_communication(9999)
