"""Unit tests for persona.application_service module."""

from typing import Any

import pytest
from psycopg import Connection


@pytest.fixture
def app_service(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    """ApplicationService backed by an empty PostgreSQL database."""
    from persona.application_service import ApplicationService

    return ApplicationService(db_conn)  # type: ignore[arg-type]


class TestApplicationServiceCreate:
    """Tests for ApplicationService.create_application."""

    def test_requires_company(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="Company is required"):
            svc.create_application({"position": "Dev"})

    def test_requires_position(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="Position is required"):
            svc.create_application({"company": "Corp"})

    def test_rejects_invalid_status(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="Invalid status"):
            svc.create_application(
                {"company": "Corp", "position": "Dev", "status": "Bogus"}
            )

    def test_accepts_valid_statuses(self, app_service: object) -> None:
        from persona.application_service import ApplicationService
        from persona.models import APPLICATION_STATUSES

        svc: ApplicationService = app_service  # type: ignore[assignment]
        for status in APPLICATION_STATUSES:
            result = svc.create_application(
                {"company": f"Corp_{status}", "position": "Dev", "status": status}
            )
            assert result["status"] == status

    def test_creates_with_defaults(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        result = svc.create_application({"company": "Corp", "position": "Dev"})

        assert result["id"] is not None
        assert result["status"] == "Interested"
        assert result["company"] == "Corp"
        assert result["position"] == "Dev"


class TestApplicationServiceGet:
    """Tests for ApplicationService.get_application."""

    def test_gets_existing_application(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        result = svc.get_application(created["id"])

        assert result["id"] == created["id"]
        assert result["company"] == "Corp"

    def test_raises_for_nonexistent(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.get_application(9999)


class TestApplicationServiceList:
    """Tests for ApplicationService.list_applications."""

    def test_lists_all(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        svc.create_application({"company": "A", "position": "P1"})
        svc.create_application({"company": "B", "position": "P2"})
        results = svc.list_applications()

        assert len(results) == 2

    def test_filter_by_status(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        svc.create_application({"company": "A", "position": "P1", "status": "Applied"})
        svc.create_application(
            {"company": "B", "position": "P2", "status": "Interested"}
        )
        results = svc.list_applications(status="Applied")

        assert len(results) == 1
        assert results[0]["company"] == "A"

    def test_search_by_query(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        svc.create_application({"company": "Acme Corp", "position": "Dev"})
        svc.create_application({"company": "Other Inc", "position": "QA"})
        results = svc.list_applications(q="acme")

        assert len(results) == 1
        assert results[0]["company"] == "Acme Corp"

    def test_returns_empty_when_no_applications(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        results = svc.list_applications()

        assert results == []


class TestApplicationServiceUpdate:
    """Tests for ApplicationService.update_application."""

    def test_updates_fields(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        updated = svc.update_application(created["id"], {"status": "Applied"})

        assert updated["status"] == "Applied"
        assert updated["company"] == "Corp"

    def test_rejects_invalid_status_on_update(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        with pytest.raises(ValueError, match="Invalid status"):
            svc.update_application(created["id"], {"status": "Fake"})

    def test_raises_for_nonexistent_app(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.update_application(9999, {"status": "Applied"})


class TestApplicationServiceDelete:
    """Tests for ApplicationService.delete_application."""

    def test_deletes_existing(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        svc.delete_application(created["id"])

        with pytest.raises(ValueError, match="not found"):
            svc.get_application(created["id"])

    def test_returns_deleted_app_data(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        result = svc.delete_application(created["id"])

        assert result["company"] == "Corp"
        assert result["position"] == "Dev"

    def test_raises_for_nonexistent(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.delete_application(9999)


class TestApplicationServiceContacts:
    """Tests for ApplicationService contact operations."""

    def test_add_contact_requires_name(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        with pytest.raises(ValueError, match="name is required"):
            svc.add_contact(created["id"], {"role": "HR"})

    def test_add_contact_returns_contact(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        contact = svc.add_contact(
            created["id"],
            {"name": "Alice", "email": "alice@corp.com"},
        )

        assert contact["name"] == "Alice"
        assert contact["email"] == "alice@corp.com"
        assert contact["app_id"] == created["id"]

    def test_list_contacts(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        svc.add_contact(created["id"], {"name": "Alice"})
        svc.add_contact(created["id"], {"name": "Bob"})
        contacts = svc.list_contacts(created["id"])

        assert len(contacts) == 2

    def test_update_contact(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        contact = svc.add_contact(created["id"], {"name": "Alice"})
        updated = svc.update_contact(contact["id"], {"role": "Engineering Manager"})

        assert updated["role"] == "Engineering Manager"
        assert updated["name"] == "Alice"

    def test_remove_contact(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        contact = svc.add_contact(created["id"], {"name": "Alice"})
        name = svc.remove_contact(contact["id"])

        assert name == "Alice"
        contacts = svc.list_contacts(created["id"])
        assert len(contacts) == 0


class TestApplicationServiceCommunications:
    """Tests for ApplicationService communication operations."""

    def test_add_communication_requires_type(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        with pytest.raises(ValueError, match="type is required"):
            svc.add_communication(
                created["id"],
                {"direction": "sent", "body": "Hello", "date": "2024-01-01"},
            )

    def test_add_communication_requires_body(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        with pytest.raises(ValueError, match="body is required"):
            svc.add_communication(
                created["id"],
                {"type": "email", "direction": "sent", "date": "2024-01-01"},
            )

    def test_add_communication_returns_record(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        comm = svc.add_communication(
            created["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Applying for the role.",
                "date": "2024-01-01",
                "subject": "Application",
            },
        )

        assert comm["id"] is not None
        assert comm["type"] == "email"
        assert comm["subject"] == "Application"

    def test_list_communications(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        svc.add_communication(
            created["id"],
            {"type": "email", "direction": "sent", "body": "A", "date": "2024-01-01"},
        )
        svc.add_communication(
            created["id"],
            {
                "type": "phone",
                "direction": "received",
                "body": "B",
                "date": "2024-02-01",
            },
        )
        comms = svc.list_communications(created["id"])

        assert len(comms) == 2

    def test_update_communication(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        comm = svc.add_communication(
            created["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Draft",
                "date": "2024-01-01",
            },
        )
        updated = svc.update_communication(comm["id"], {"status": "draft"})

        assert updated["status"] == "draft"

    def test_remove_communication(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        comm = svc.add_communication(
            created["id"],
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
        comms = svc.list_communications(created["id"])
        assert len(comms) == 0


class TestApplicationServiceContext:
    """Tests for ApplicationService.get_application_context."""

    def test_returns_composite_data(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        svc.add_contact(created["id"], {"name": "Alice"})
        svc.add_communication(
            created["id"],
            {"type": "email", "direction": "sent", "body": "Hi", "date": "2024-01-01"},
        )
        context = svc.get_application_context(created["id"])

        assert "application" in context
        assert "contacts" in context
        assert "communications" in context
        assert "resume_version" in context
        assert "default_resume" in context

    def test_application_data_matches(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        context = svc.get_application_context(created["id"])

        assert context["application"]["id"] == created["id"]
        assert context["application"]["company"] == "Corp"

    def test_contacts_list_in_context(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        svc.add_contact(created["id"], {"name": "Bob"})
        context = svc.get_application_context(created["id"])

        assert len(context["contacts"]) == 1
        assert context["contacts"][0]["name"] == "Bob"

    def test_default_resume_included(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        created = svc.create_application({"company": "Corp", "position": "Dev"})
        context = svc.get_application_context(created["id"])

        # default_resume should be populated since migration creates a default version
        assert context["default_resume"] is not None

    def test_raises_for_nonexistent_app(self, app_service: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_service  # type: ignore[assignment]
        with pytest.raises(ValueError, match="not found"):
            svc.get_application_context(9999)
