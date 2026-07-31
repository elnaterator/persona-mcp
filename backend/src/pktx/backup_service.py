"""Full-database logical backup: per-table CSV in a gzipped tar archive.

Deliberately avoids ``pg_dump``: the Lambda image carries no PostgreSQL client
binaries, and a client/server version mismatch against Neon would be a silent
failure mode. ``COPY ... TO STDOUT`` over the existing psycopg connection
produces text that ``COPY ... FROM STDIN`` reloads verbatim.

The archive is data-only. Schema comes from ``migrations.py``, which is already
how every environment is built — the manifest records the schema version the
data was dumped at so a restore can refuse a mismatch.
"""

import io
import json
import logging
import tarfile
import time
from datetime import datetime, timezone
from typing import Any

from psycopg import sql

from pktx.db import DBConnection
from pktx.migrations import SCHEMA_VERSION

logger = logging.getLogger("pktx")

MANIFEST_NAME = "manifest.json"

# Every application table, ordered so a sequential restore never violates a
# foreign key: parents first, the polymorphic link table last. `schema_version`
# is excluded — migrations own it, and the manifest carries the version.
#
# tests/unit/test_backup_service.py::test_table_list_covers_live_schema asserts
# this list matches the tables a fully migrated database actually has, so a new
# migration cannot silently drop a table out of the backup.
TABLES_IN_FK_ORDER: tuple[str, ...] = (
    "users",
    "resume_version",
    "application",
    "accomplishment",
    "note",
    "contact",
    "communication",
    "resource_link",
    "oauth_kv",
)

# Tables whose primary key is a SERIAL — their sequences must be re-synced after
# a restore that inserts explicit ids.
SERIAL_ID_TABLES: tuple[str, ...] = (
    "resume_version",
    "application",
    "accomplishment",
    "note",
    "contact",
    "communication",
)

EXCLUDED_TABLES: frozenset[str] = frozenset({"schema_version"})


def _pktx_version() -> str:
    try:
        from importlib.metadata import version

        return version("pktx")
    except Exception:  # pragma: no cover - packaging metadata absent
        return "unknown"


def live_tables(conn: DBConnection) -> set[str]:
    """Return the public tables that currently exist in the database."""
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    ).fetchall()
    names = {row["table_name"] if isinstance(row, dict) else row[0] for row in rows}
    return names - EXCLUDED_TABLES


def _dump_table(conn: DBConnection, table: str) -> bytes:
    """Return one table as CSV-with-header bytes."""
    buf = io.BytesIO()
    stmt = sql.SQL("COPY {} TO STDOUT (FORMAT CSV, HEADER)").format(
        sql.Identifier(table)
    )
    with conn.cursor() as cur:
        with cur.copy(stmt) as copy:
            for block in copy:
                buf.write(bytes(block))
    return buf.getvalue()


def _row_count(conn: DBConnection, table: str) -> int:
    stmt = sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))
    row = conn.execute(stmt).fetchone()  # type: ignore[arg-type]
    return int(row["n"] if isinstance(row, dict) else row[0])


def _add_file(tar: tarfile.TarFile, name: str, data: bytes, mtime: float) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    info.mtime = int(mtime)
    tar.addfile(info, io.BytesIO(data))


def create_backup(conn: DBConnection) -> tuple[bytes, dict[str, Any]]:
    """Dump every application table into a gzipped tar archive.

    Returns the archive bytes and its manifest. Any table failure propagates —
    a partial archive is never returned, so the caller cannot upload one.
    """
    tables = [t for t in TABLES_IN_FK_ORDER if t in live_tables(conn)]
    now = datetime.now(timezone.utc)
    mtime = time.time()

    counts: dict[str, int] = {}
    dumps: dict[str, bytes] = {}
    for table in tables:
        dumps[table] = _dump_table(conn, table)
        counts[table] = _row_count(conn, table)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now.isoformat(),
        "pktx_version": _pktx_version(),
        "table_order": tables,
        "tables": counts,
    }

    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz") as tar:
        _add_file(
            tar,
            MANIFEST_NAME,
            json.dumps(manifest, indent=2).encode("utf-8"),
            mtime,
        )
        for table in tables:
            _add_file(tar, f"tables/{table}.csv", dumps[table], mtime)

    return archive.getvalue(), manifest


def backup_key(environment: str, when: datetime | None = None) -> str:
    """Build the S3 object key for a backup taken at ``when``."""
    ts = when or datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%dT%H%M%SZ")
    return f"backups/{ts:%Y}/{ts:%m}/pktx-{environment}-{stamp}.tar.gz"


def upload_backup(
    data: bytes,
    bucket: str,
    key: str,
    s3_client: Any | None = None,
) -> None:
    """Upload archive bytes to S3. ``s3_client`` is injectable for tests."""
    client = s3_client
    if client is None:  # pragma: no cover - exercised in deployed environments
        import boto3

        client = boto3.client("s3")
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType="application/gzip",
    )


def run_backup(
    conn: DBConnection,
    bucket: str,
    environment: str,
    s3_client: Any | None = None,
) -> dict[str, Any]:
    """Create a backup and upload it. Returns the result summary."""
    started = time.monotonic()
    data, manifest = create_backup(conn)
    key = backup_key(environment)
    upload_backup(data, bucket, key, s3_client=s3_client)
    elapsed_ms = int((time.monotonic() - started) * 1000)
    result = {
        "key": key,
        "bytes": len(data),
        "tables": manifest["tables"],
        "schema_version": manifest["schema_version"],
        "elapsed_ms": elapsed_ms,
    }
    logger.info(
        "backup complete bucket=%s key=%s bytes=%d rows=%d elapsed_ms=%d",
        bucket,
        key,
        len(data),
        sum(manifest["tables"].values()),
        elapsed_ms,
    )
    return result
