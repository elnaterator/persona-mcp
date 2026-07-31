"""Backup → restore round trip: the proof that a backup is actually restorable.

Seeds one database with data across every resource type, dumps it, restores the
archive into a second (empty) database, and compares. A backup nobody has
restored is not a backup.
"""

import json
from collections.abc import Generator
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest
from psycopg import Connection, sql
from psycopg.rows import dict_row

from pktx.backup_service import TABLES_IN_FK_ORDER, create_backup
from pktx.restore_service import RestoreError, restore_archive, unpack

_USER = "restore_user"
_OTHER = "restore_other"


@pytest.fixture
def restore_dsn(pg_dsn: str) -> Generator[str, None, None]:
    """Create an empty scratch database in the session container, and drop it after.

    A second database is equivalent to a second container for this test and
    costs nothing — the restore target only has to be empty and separate.
    """
    parts = urlsplit(pg_dsn)
    name = "pktx_restore_target"
    with psycopg.connect(pg_dsn, autocommit=True) as admin:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
        admin.execute(f'CREATE DATABASE "{name}"')
    try:
        yield urlunsplit(parts._replace(path=f"/{name}"))
    finally:
        with psycopg.connect(pg_dsn, autocommit=True) as admin:
            admin.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (name,),
            )
            admin.execute(f'DROP DATABASE IF EXISTS "{name}"')


@pytest.fixture
def seeded(db_conn: Connection[Any]) -> dict[str, Any]:
    """Populate one user with every resource type, plus a second user's data."""
    from pktx.accomplishment_service import AccomplishmentService
    from pktx.application_service import ApplicationService
    from pktx.communication_service import ContactCommunicationService
    from pktx.contact_service import ContactService
    from pktx.link_service import LinkService
    from pktx.note_service import NoteService
    from pktx.resume_service import ResumeService

    conn: Any = db_conn
    for uid in (_USER, _OTHER):
        conn.execute(
            "INSERT INTO users (id, email) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (uid, f"{uid}@test.com"),
        )

    resumes = ResumeService(conn)
    apps = ApplicationService(conn)
    accs = AccomplishmentService(conn)
    notes = NoteService(conn)
    contacts = ContactService(conn)
    comms = ContactCommunicationService(conn)
    links = LinkService(conn)

    resume = resumes.create_resume("Backend Resume", user_id=_USER)
    resumes.update_section(
        "summary",
        {"text": "Staff engineer who tests restores."},
        version_id=resume["id"],
        user_id=_USER,
    )
    app = apps.create_application(
        {"company": "Acme", "position": "Staff Engineer", "tags": ["remote"]},
        user_id=_USER,
    )
    acc = accs.create_accomplishment(
        {
            "title": "Proved the restore path",
            "situation": "Backups existed but had never been restored",
            "task": "Prove it",
            "action": "Wrote a round-trip test",
            "result": "Restore verified",
            "tags": ["ops"],
        },
        user_id=_USER,
    )
    note = notes.create_note(
        {"title": "Runbook notes", "content": "Restore into a scratch DB first."},
        user_id=_USER,
    )
    contact = contacts.create_contact(
        {"name": "Dana Ops", "email": "dana@example.com", "company": "Acme"},
        user_id=_USER,
    )
    comm = comms.add_for_contact(
        contact["id"],
        {
            "type": "email",
            "direction": "sent",
            "subject": "Restore drill",
            "body": "Scheduling the drill for Friday.",
            "date": "2026-07-30",
        },
        user_id=_USER,
    )
    links.link("application", app["id"], "resume", resume["id"], _USER)
    links.link("accomplishment", acc["id"], "application", app["id"], _USER)

    # Second user's data must survive the round trip untouched too.
    notes.create_note({"title": "Other user note", "content": "hi"}, user_id=_OTHER)

    # No commit: db_conn rolls back after the test, and the backup runs on this
    # same connection, so it sees the uncommitted rows.
    return {
        "resume": resume,
        "application": app,
        "accomplishment": acc,
        "note": note,
        "contact": contact,
        "communication": comm,
    }


def _counts(conn: Connection[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for table in TABLES_IN_FK_ORDER:
        row = conn.execute(
            sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))
        ).fetchone()
        out[table] = int(row["n"])  # type: ignore[index]
    return out


class TestBackupRestoreRoundTrip:
    def test_row_counts_match_after_restore(
        self, db_conn: Connection[Any], seeded: dict[str, Any], restore_dsn: str
    ) -> None:
        source_counts = _counts(db_conn)
        data, _ = create_backup(db_conn)  # type: ignore[arg-type]

        restored_counts = restore_archive(data, restore_dsn)

        assert restored_counts == source_counts
        assert restored_counts["users"] >= 2
        assert restored_counts["communication"] >= 1
        assert restored_counts["resource_link"] >= 2

    def test_restored_records_match_field_for_field(
        self, db_conn: Connection[Any], seeded: dict[str, Any], restore_dsn: str
    ) -> None:
        from pktx.accomplishment_service import AccomplishmentService
        from pktx.application_service import ApplicationService
        from pktx.communication_service import ContactCommunicationService
        from pktx.contact_service import ContactService
        from pktx.link_service import LinkService
        from pktx.note_service import NoteService
        from pktx.resume_service import ResumeService

        data, _ = create_backup(db_conn)  # type: ignore[arg-type]
        restore_archive(data, restore_dsn)

        with psycopg.connect(
            restore_dsn,
            row_factory=dict_row,  # type: ignore[arg-type]
        ) as target:
            conn: Any = target
            assert ResumeService(conn).get_resume(
                seeded["resume"]["id"], user_id=_USER
            ) == ResumeService(db_conn).get_resume(  # type: ignore[arg-type]
                seeded["resume"]["id"], user_id=_USER
            )
            assert ApplicationService(conn).get_application(
                seeded["application"]["id"], user_id=_USER
            ) == ApplicationService(db_conn).get_application(  # type: ignore[arg-type]
                seeded["application"]["id"], user_id=_USER
            )
            assert AccomplishmentService(conn).get_accomplishment(
                seeded["accomplishment"]["id"], user_id=_USER
            ) == AccomplishmentService(db_conn).get_accomplishment(  # type: ignore[arg-type]
                seeded["accomplishment"]["id"], user_id=_USER
            )
            assert NoteService(conn).get_note(
                seeded["note"]["id"], user_id=_USER
            ) == NoteService(db_conn).get_note(  # type: ignore[arg-type]
                seeded["note"]["id"], user_id=_USER
            )
            assert ContactService(conn).get_contact(
                seeded["contact"]["id"], user_id=_USER
            ) == ContactService(db_conn).get_contact(  # type: ignore[arg-type]
                seeded["contact"]["id"], user_id=_USER
            )
            assert ContactCommunicationService(conn).list_for_contact(
                seeded["contact"]["id"], user_id=_USER
            ) == ContactCommunicationService(db_conn).list_for_contact(  # type: ignore[arg-type]
                seeded["contact"]["id"], user_id=_USER
            )
            assert LinkService(conn).list_all(_USER) == LinkService(
                db_conn  # type: ignore[arg-type]
            ).list_all(_USER)

    def test_sequences_advance_past_restored_ids(
        self, db_conn: Connection[Any], seeded: dict[str, Any], restore_dsn: str
    ) -> None:
        """Without setval, the first insert after a restore collides on the PK."""
        from pktx.note_service import NoteService

        data, _ = create_backup(db_conn)  # type: ignore[arg-type]
        restore_archive(data, restore_dsn)

        with psycopg.connect(
            restore_dsn,
            row_factory=dict_row,  # type: ignore[arg-type]
        ) as target:
            new_note = NoteService(target).create_note(  # type: ignore[arg-type]
                {"title": "post-restore", "content": "still works"}, user_id=_USER
            )

        assert new_note["id"] > seeded["note"]["id"]

    def test_restore_is_idempotent(
        self, db_conn: Connection[Any], seeded: dict[str, Any], restore_dsn: str
    ) -> None:
        """Restoring twice truncates first, so counts do not double."""
        data, _ = create_backup(db_conn)  # type: ignore[arg-type]

        first = restore_archive(data, restore_dsn)
        second = restore_archive(data, restore_dsn)

        assert first == second


class TestArchiveValidation:
    def test_schema_version_mismatch_is_refused(
        self, db_conn: Connection[Any], restore_dsn: str
    ) -> None:
        import io
        import tarfile

        data, manifest = create_backup(db_conn)  # type: ignore[arg-type]
        _, tables = unpack(data)
        manifest["schema_version"] = 999

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            payload = json.dumps(manifest).encode()
            info = tarfile.TarInfo("manifest.json")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
            for name, csv in tables.items():
                info = tarfile.TarInfo(f"tables/{name}.csv")
                info.size = len(csv)
                tar.addfile(info, io.BytesIO(csv))

        with pytest.raises(RestoreError, match="schema v999"):
            restore_archive(buf.getvalue(), restore_dsn)

    def test_archive_without_manifest_is_rejected(self) -> None:
        import io
        import tarfile

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            info = tarfile.TarInfo("tables/users.csv")
            info.size = 3
            tar.addfile(info, io.BytesIO(b"id\n"))

        with pytest.raises(RestoreError, match="no manifest"):
            unpack(buf.getvalue())
