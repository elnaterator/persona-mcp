"""Unit tests for backup_service: table coverage, manifest, archive shape, upload."""

import io
import json
import tarfile
from typing import Any

import pytest
from psycopg import Connection

from pktx.backup_service import (
    MANIFEST_NAME,
    SERIAL_ID_TABLES,
    TABLES_IN_FK_ORDER,
    backup_key,
    create_backup,
    live_tables,
    run_backup,
    upload_backup,
)
from pktx.migrations import SCHEMA_VERSION


class FakeS3:
    """Minimal stand-in for the boto3 S3 client — no network in CI."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"ETag": "fake"}


def _user_count(conn: Connection[Any]) -> int:
    """Row count in `users` — the v3→v4 migration seeds a 'legacy' row."""
    row = conn.execute("SELECT count(*) AS n FROM users").fetchone()
    return int(row["n"])  # type: ignore[index]


def _members(data: bytes) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            fh = tar.extractfile(member)
            assert fh is not None
            out[member.name] = fh.read()
    return out


class TestTableCoverage:
    def test_table_list_covers_live_schema(self, db_conn: Connection[Any]) -> None:
        """A new migration must not silently drop a table out of the backup."""
        assert live_tables(db_conn) == set(TABLES_IN_FK_ORDER)  # type: ignore[arg-type]

    def test_users_first_and_links_last(self) -> None:
        assert TABLES_IN_FK_ORDER[0] == "users"
        assert TABLES_IN_FK_ORDER.index("contact") < TABLES_IN_FK_ORDER.index(
            "communication"
        )
        assert TABLES_IN_FK_ORDER.index("resource_link") == len(TABLES_IN_FK_ORDER) - 2

    def test_serial_tables_are_backed_up(self) -> None:
        assert set(SERIAL_ID_TABLES).issubset(set(TABLES_IN_FK_ORDER))


class TestCreateBackup:
    def test_manifest_shape(self, db_conn: Connection[Any]) -> None:
        before = _user_count(db_conn)
        db_conn.execute("INSERT INTO users (id, email) VALUES ('u1', 'u1@test.com')")

        data, manifest = create_backup(db_conn)  # type: ignore[arg-type]

        assert manifest["schema_version"] == SCHEMA_VERSION
        assert manifest["table_order"] == list(TABLES_IN_FK_ORDER)
        assert manifest["tables"]["users"] == before + 1
        assert set(manifest["tables"]) == set(TABLES_IN_FK_ORDER)
        assert manifest["created_at"].endswith("+00:00")
        assert data[:2] == b"\x1f\x8b"  # gzip magic

    def test_archive_contains_manifest_and_every_table(
        self, db_conn: Connection[Any]
    ) -> None:
        data, _ = create_backup(db_conn)  # type: ignore[arg-type]

        names = _members(data)
        assert MANIFEST_NAME in names
        for table in TABLES_IN_FK_ORDER:
            assert f"tables/{table}.csv" in names

    def test_csv_carries_header_and_rows(self, db_conn: Connection[Any]) -> None:
        before = _user_count(db_conn)
        db_conn.execute(
            "INSERT INTO users (id, email) VALUES ('u1', 'u1@test.com'), "
            "('u2', 'u2@test.com')"
        )

        data, manifest = create_backup(db_conn)  # type: ignore[arg-type]

        csv = _members(data)["tables/users.csv"].decode()
        header, *rows = csv.strip().splitlines()
        assert header.split(",")[:2] == ["id", "email"]
        assert len(rows) == before + 2
        assert manifest["tables"]["users"] == before + 2
        assert any(line.startswith("u1,u1@test.com") for line in rows)

    def test_manifest_is_valid_json(self, db_conn: Connection[Any]) -> None:
        data, manifest = create_backup(db_conn)  # type: ignore[arg-type]

        assert json.loads(_members(data)[MANIFEST_NAME]) == manifest


class TestBackupKey:
    def test_key_is_date_partitioned(self) -> None:
        from datetime import datetime, timezone

        when = datetime(2026, 7, 31, 4, 5, 6, tzinfo=timezone.utc)

        assert backup_key("prod", when) == (
            "backups/2026/07/pktx-prod-20260731T040506Z.tar.gz"
        )


class TestUpload:
    def test_upload_passes_bytes_and_content_type(self) -> None:
        s3 = FakeS3()

        upload_backup(b"payload", "bkt", "some/key.tar.gz", s3_client=s3)

        assert s3.calls == [
            {
                "Bucket": "bkt",
                "Key": "some/key.tar.gz",
                "Body": b"payload",
                "ContentType": "application/gzip",
            }
        ]

    def test_run_backup_uploads_and_summarizes(self, db_conn: Connection[Any]) -> None:
        before = _user_count(db_conn)
        db_conn.execute("INSERT INTO users (id, email) VALUES ('u1', 'u1@test.com')")
        s3 = FakeS3()

        result = run_backup(db_conn, "bkt", "dev", s3_client=s3)  # type: ignore[arg-type]

        assert len(s3.calls) == 1
        assert result["key"].startswith("backups/")
        assert result["bytes"] == len(s3.calls[0]["Body"])
        assert result["tables"]["users"] == before + 1
        assert result["schema_version"] == SCHEMA_VERSION

    def test_dump_failure_uploads_nothing(
        self, db_conn: Connection[Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A partial archive must never reach S3."""
        s3 = FakeS3()

        def boom(conn: Any, table: str) -> bytes:
            if table == "note":
                raise RuntimeError("disk on fire")
            return b"id\n"

        monkeypatch.setattr("pktx.backup_service._dump_table", boom)

        with pytest.raises(RuntimeError, match="disk on fire"):
            run_backup(db_conn, "bkt", "dev", s3_client=s3)  # type: ignore[arg-type]

        assert s3.calls == []
