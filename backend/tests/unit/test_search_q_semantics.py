"""T14: Regression tests for word-split AND q semantics across resources."""

from typing import Any

import pytest
from psycopg import Connection


@pytest.fixture
def app_svc(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    from persona.application_service import ApplicationService

    return ApplicationService(db_conn)  # type: ignore[arg-type]


@pytest.fixture
def acc_svc(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    from persona.accomplishment_service import AccomplishmentService

    return AccomplishmentService(db_conn)  # type: ignore[arg-type]


@pytest.fixture
def note_svc(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    from persona.note_service import NoteService

    return NoteService(db_conn)  # type: ignore[arg-type]


@pytest.fixture
def contact_svc(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    from persona.contact_service import ContactService

    return ContactService(db_conn)  # type: ignore[arg-type]


class TestApplicationWordSplitQ:
    def test_single_word_matches(self, app_svc: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_svc  # type: ignore[assignment]
        svc.create_application({"company": "Acme Corp", "position": "Engineer"})
        svc.create_application({"company": "Beta Ltd", "position": "Designer"})
        results = svc.list_applications(q="acme")
        assert len(results) == 1
        assert results[0]["company"] == "Acme Corp"

    def test_multi_word_and_both_words_must_match(self, app_svc: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_svc  # type: ignore[assignment]
        svc.create_application({"company": "Acme Corp", "position": "Engineer"})
        svc.create_application({"company": "Acme Ltd", "position": "Designer"})
        # "acme engineer" — only first matches position containing "engineer"
        results = svc.list_applications(q="acme engineer")
        assert len(results) == 1
        assert results[0]["company"] == "Acme Corp"

    def test_multi_word_no_match_if_only_one_word(self, app_svc: object) -> None:
        from persona.application_service import ApplicationService

        svc: ApplicationService = app_svc  # type: ignore[assignment]
        svc.create_application({"company": "Acme Corp", "position": "Engineer"})
        results = svc.list_applications(q="acme nomatch")
        assert len(results) == 0


class TestAccomplishmentWordSplitQ:
    def test_single_word_matches_title(self, acc_svc: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_svc  # type: ignore[assignment]
        svc.create_accomplishment({"title": "Launched product", "result": "10x growth"})
        svc.create_accomplishment({"title": "Hired team", "result": "built great team"})
        results = svc.list_accomplishments(q="launched")
        assert len(results) == 1
        assert results[0]["title"] == "Launched product"

    def test_multi_word_and_across_fields(self, acc_svc: object) -> None:
        from persona.accomplishment_service import AccomplishmentService

        svc: AccomplishmentService = acc_svc  # type: ignore[assignment]
        svc.create_accomplishment({"title": "Launched product", "result": "10x growth"})
        svc.create_accomplishment(
            {"title": "Launched campaign", "result": "5x revenue"}
        )
        # "launched growth" — only first has "growth" in result
        results = svc.list_accomplishments(q="launched growth")
        assert len(results) == 1
        assert results[0]["title"] == "Launched product"


class TestCommunicationWordSplitQ:
    def test_single_word_matches_subject(self, db_conn: Connection[Any]) -> None:
        from persona.communication_service import ContactCommunicationService
        from persona.contact_service import ContactService

        contact_svc = ContactService(db_conn)  # type: ignore[arg-type]
        comm_svc = ContactCommunicationService(db_conn)  # type: ignore[arg-type]

        contact = contact_svc.create_contact({"name": "Alice Smith"})
        comm_svc.add_for_contact(
            contact["id"],
            {
                "type": "email",
                "direction": "sent",
                "subject": "UniqueSubject hello",
                "body": "some body",
                "date": "2024-01-01",
            },
        )
        results = comm_svc.search(q="UniqueSubject")
        assert len(results) == 1

    def test_multi_word_and_both_must_match(self, db_conn: Connection[Any]) -> None:
        from persona.communication_service import ContactCommunicationService
        from persona.contact_service import ContactService

        contact_svc = ContactService(db_conn)  # type: ignore[arg-type]
        comm_svc = ContactCommunicationService(db_conn)  # type: ignore[arg-type]

        contact = contact_svc.create_contact({"name": "Bob Jones"})
        comm_svc.add_for_contact(
            contact["id"],
            {
                "type": "email",
                "direction": "sent",
                "subject": "Alpha subject",
                "body": "beta content",
                "date": "2024-01-01",
            },
        )
        comm_svc.add_for_contact(
            contact["id"],
            {
                "type": "email",
                "direction": "sent",
                "subject": "Alpha subject only",
                "body": "other content",
                "date": "2024-01-02",
            },
        )
        # "alpha beta" — only first has "beta" in body
        results = comm_svc.search(q="alpha beta")
        assert len(results) == 1
        assert results[0]["subject"] == "Alpha subject"
