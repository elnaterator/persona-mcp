"""Unit tests for LinkService — canonical ordering, validation, counts."""

from typing import Any

import pytest
from psycopg import Connection

_USER_A = "link_unit_user_a"
_USER_B = "link_unit_user_b"


@pytest.fixture
def seeded_db(db_conn: Connection[Any]) -> Connection[Any]:
    db_conn.execute(
        "INSERT INTO users (id, email) VALUES (%s, %s), (%s, %s) "
        "ON CONFLICT (id) DO NOTHING",
        (_USER_A, "a@test.com", _USER_B, "b@test.com"),
    )
    return db_conn


@pytest.fixture
def link_service(seeded_db: Connection[Any]) -> Any:
    from pktx.link_service import LinkService

    return LinkService(seeded_db)  # type: ignore[arg-type]


def _make_note(db_conn: Connection[Any], title: str, uid: str) -> int:
    row = db_conn.execute(
        "INSERT INTO note (title, content, user_id) VALUES (%s, '', %s) RETURNING id",
        (title, uid),
    ).fetchone()
    assert row is not None
    return int(row["id"])


def _make_application(db_conn: Connection[Any], uid: str) -> int:
    row = db_conn.execute(
        "INSERT INTO application (company, position, status, user_id) "
        "VALUES ('Co', 'Dev', 'Interested', %s) RETURNING id",
        (uid,),
    ).fetchone()
    assert row is not None
    return int(row["id"])


def _make_contact(db_conn: Connection[Any], uid: str) -> int:
    row = db_conn.execute(
        "INSERT INTO contact (name, user_id) VALUES ('Person', %s) RETURNING id",
        (uid,),
    ).fetchone()
    assert row is not None
    return int(row["id"])


# ── canonical ordering ────────────────────────────────────────────────────────


class TestCanonicalize:
    def test_note_application_stays_canonical(self) -> None:
        from pktx.link_service import canonicalize

        # 'application' < 'note' lexicographically
        result = canonicalize("note", 1, "application", 2)
        assert result == ("application", 2, "note", 1)

    def test_already_canonical_unchanged(self) -> None:
        from pktx.link_service import canonicalize

        result = canonicalize("application", 1, "note", 2)
        assert result == ("application", 1, "note", 2)

    def test_same_type_lower_id_left(self) -> None:
        from pktx.link_service import canonicalize

        result = canonicalize("note", 5, "note", 3)
        assert result == ("note", 3, "note", 5)

    def test_same_type_already_ordered(self) -> None:
        from pktx.link_service import canonicalize

        result = canonicalize("note", 1, "note", 9)
        assert result == ("note", 1, "note", 9)


# ── self-link rejection ───────────────────────────────────────────────────────


class TestLinkValidation:
    def test_rejects_self_link(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note_id = _make_note(seeded_db, "Self", _USER_A)
        with pytest.raises(ValueError, match="itself"):
            link_service.link("note", note_id, "note", note_id, _USER_A)

    def test_rejects_invalid_type(self, link_service: Any) -> None:
        with pytest.raises(ValueError, match="[Ii]nvalid"):
            link_service.link("widget", 1, "note", 2, _USER_A)

    def test_rejects_cross_user_ownership(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note_a = _make_note(seeded_db, "Note A", _USER_A)
        note_b = _make_note(seeded_db, "Note B", _USER_B)
        # USER_A trying to link USER_B's note
        with pytest.raises(ValueError, match="not found|not owned"):
            link_service.link("note", note_a, "note", note_b, _USER_A)

    def test_link_idempotent(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note = _make_note(seeded_db, "Idem", _USER_A)
        app = _make_application(seeded_db, _USER_A)
        link_service.link("note", note, "application", app, _USER_A)
        # Second call must not raise
        link_service.link("note", note, "application", app, _USER_A)
        links = link_service.list_links("note", note, _USER_A)
        assert len(links.get("application", [])) == 1


# ── list_links ────────────────────────────────────────────────────────────────


class TestListLinks:
    def test_shows_linked_resource(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note = _make_note(seeded_db, "My Note", _USER_A)
        app = _make_application(seeded_db, _USER_A)
        link_service.link("note", note, "application", app, _USER_A)
        links = link_service.list_links("note", note, _USER_A)
        assert "application" in links
        assert any(r.id == app for r in links["application"])

    def test_bidirectional(self, seeded_db: Connection[Any], link_service: Any) -> None:
        note = _make_note(seeded_db, "Bi Note", _USER_A)
        app = _make_application(seeded_db, _USER_A)
        link_service.link("note", note, "application", app, _USER_A)
        from_app = link_service.list_links("application", app, _USER_A)
        assert "note" in from_app

    def test_empty_when_no_links(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note = _make_note(seeded_db, "Lonely", _USER_A)
        assert link_service.list_links("note", note, _USER_A) == {}

    def test_unlink_removes_from_list(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note = _make_note(seeded_db, "Unlink Me", _USER_A)
        app = _make_application(seeded_db, _USER_A)
        link_service.link("note", note, "application", app, _USER_A)
        link_service.unlink("note", note, "application", app, _USER_A)
        assert link_service.list_links("note", note, _USER_A) == {}


# ── count_links ───────────────────────────────────────────────────────────────


class TestCountLinks:
    def test_bulk_count(self, seeded_db: Connection[Any], link_service: Any) -> None:
        note1 = _make_note(seeded_db, "Count1", _USER_A)
        note2 = _make_note(seeded_db, "Count2", _USER_A)
        note3 = _make_note(seeded_db, "Count3", _USER_A)
        app = _make_application(seeded_db, _USER_A)
        link_service.link("note", note1, "application", app, _USER_A)
        link_service.link("note", note2, "application", app, _USER_A)
        counts = link_service.count_links("note", [note1, note2, note3], _USER_A)
        assert counts.get(note1, 0) == 1
        assert counts.get(note2, 0) == 1
        assert counts.get(note3, 0) == 0

    def test_count_isolates_by_user(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note_a = _make_note(seeded_db, "A's note", _USER_A)
        note_b = _make_note(seeded_db, "B's note", _USER_B)
        app_a = _make_application(seeded_db, _USER_A)
        # Only USER_A's link
        link_service.link("note", note_a, "application", app_a, _USER_A)
        counts_b = link_service.count_links("note", [note_b], _USER_B)
        assert counts_b.get(note_b, 0) == 0


# ── unlink_all ────────────────────────────────────────────────────────────────


class TestUnlinkAll:
    def test_unlink_all_removes_every_link(
        self, seeded_db: Connection[Any], link_service: Any
    ) -> None:
        note = _make_note(seeded_db, "Multi", _USER_A)
        app = _make_application(seeded_db, _USER_A)
        contact = _make_contact(seeded_db, _USER_A)
        link_service.link("note", note, "application", app, _USER_A)
        link_service.link("contact", contact, "note", note, _USER_A)
        link_service.unlink_all("note", note, _USER_A)
        assert link_service.list_links("note", note, _USER_A) == {}
        assert link_service.list_links("application", app, _USER_A) == {}
