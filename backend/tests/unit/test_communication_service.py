"""Unit tests for ContactCommunicationService."""

from typing import Any

import pytest
from psycopg import Connection

_TEST_USER = "test_comm_user"
_OTHER_USER = "other_comm_user"


@pytest.fixture
def comm_service(db_conn: Connection[Any]):  # type: ignore[no-untyped-def]
    from persona.auth import current_user_id_var
    from persona.communication_service import ContactCommunicationService

    db_conn.execute(
        "INSERT INTO users (id, email) VALUES (%s, 'a@test.com') "
        "ON CONFLICT (id) DO NOTHING",
        (_TEST_USER,),
    )
    db_conn.execute(
        "INSERT INTO users (id, email) VALUES (%s, 'b@test.com') "
        "ON CONFLICT (id) DO NOTHING",
        (_OTHER_USER,),
    )
    token = current_user_id_var.set(_TEST_USER)
    yield ContactCommunicationService(db_conn)  # type: ignore[arg-type]
    current_user_id_var.reset(token)


@pytest.fixture
def contact_id(db_conn: Connection[Any]) -> int:
    row = db_conn.execute(
        "INSERT INTO contact (user_id, name) VALUES (%s, %s) RETURNING id",
        (_TEST_USER, "Alice"),
    ).fetchone()
    assert row is not None
    return row["id"]


@pytest.fixture
def other_contact_id(db_conn: Connection[Any]) -> int:
    row = db_conn.execute(
        "INSERT INTO contact (user_id, name) VALUES (%s, %s) RETURNING id",
        (_OTHER_USER, "Bob"),
    ).fetchone()
    assert row is not None
    return row["id"]


_VALID = {
    "type": "email",
    "direction": "sent",
    "body": "Hello",
    "date": "2025-01-15",
}


class TestCheckConstraint:
    def test_check_constraint_exists(self, db_conn: Connection[Any]) -> None:
        """communication_parent_xor CHECK constraint is present in schema."""
        row = db_conn.execute(
            "SELECT 1 FROM information_schema.table_constraints "
            "WHERE table_name = 'communication' "
            "AND constraint_name = 'communication_parent_xor'"
        ).fetchone()
        assert row is not None

    def test_both_null_violates_check(self, db_conn: Connection[Any]) -> None:
        with pytest.raises(Exception):
            db_conn.execute(
                "INSERT INTO communication "
                "(type, direction, body, date, status, tags) "
                "VALUES ('email', 'sent', 'x', '2025-01-01', 'sent', '[]')"
            )
            db_conn.commit()


class TestTagNormalization:
    def test_tags_lowercased(self, comm_service: Any, contact_id: int) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        result = svc.add_for_contact(
            contact_id,
            {**_VALID, "tags": ["  Recruiter  ", "PYTHON"]},
            user_id=_TEST_USER,
        )
        assert result["tags"] == ["recruiter", "python"]

    def test_duplicate_tags_deduplicated(
        self, comm_service: Any, contact_id: int
    ) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        result = svc.add_for_contact(
            contact_id,
            {**_VALID, "tags": ["foo", "foo", "FOO"]},
            user_id=_TEST_USER,
        )
        assert result["tags"] == ["foo"]

    def test_tag_over_50_chars_raises(self, comm_service: Any, contact_id: int) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        with pytest.raises(ValueError, match="50 characters"):
            svc.add_for_contact(
                contact_id,
                {**_VALID, "tags": ["a" * 51]},
                user_id=_TEST_USER,
            )


class TestDateValidator:
    def test_invalid_date_format_raises(
        self, comm_service: Any, contact_id: int
    ) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            svc.add_for_contact(
                contact_id,
                {**_VALID, "date": "15/01/2025"},
                user_id=_TEST_USER,
            )

    def test_missing_date_raises(self, comm_service: Any, contact_id: int) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        with pytest.raises(ValueError, match="date"):
            svc.add_for_contact(
                contact_id,
                {k: v for k, v in _VALID.items() if k != "date"},
                user_id=_TEST_USER,
            )


class TestTypeDirectionValidation:
    def test_invalid_type_raises(self, comm_service: Any, contact_id: int) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        with pytest.raises(ValueError, match="type"):
            svc.add_for_contact(
                contact_id,
                {**_VALID, "type": "fax"},
                user_id=_TEST_USER,
            )

    def test_invalid_direction_raises(self, comm_service: Any, contact_id: int) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        with pytest.raises(ValueError, match="direction"):
            svc.add_for_contact(
                contact_id,
                {**_VALID, "direction": "outbound"},
                user_id=_TEST_USER,
            )


class TestSearchTagAnd:
    def test_multi_tag_and_filters(self, comm_service: Any, contact_id: int) -> None:
        from persona.communication_service import ContactCommunicationService

        svc: ContactCommunicationService = comm_service
        svc.add_for_contact(
            contact_id,
            {**_VALID, "tags": ["foo", "bar"]},
            user_id=_TEST_USER,
        )
        svc.add_for_contact(contact_id, {**_VALID, "tags": ["foo"]}, user_id=_TEST_USER)

        results = svc.search(tags=["foo", "bar"], user_id=_TEST_USER)
        assert len(results) == 1
        assert "bar" in results[0]["tags"]
