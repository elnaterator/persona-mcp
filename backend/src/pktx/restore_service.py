"""Restore a pktx backup archive into a PostgreSQL database.

The inverse of :mod:`pktx.backup_service`. The target is migrated to the
archive's schema version, its application tables are truncated, and each table
is reloaded with ``COPY ... FROM STDIN`` inside one transaction — a failure
anywhere leaves the target exactly as it was.

Restoring is destructive: every table listed in the archive manifest is
truncated first.
"""

import io
import json
import logging
import tarfile
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from pktx.backup_service import MANIFEST_NAME, SERIAL_ID_TABLES
from pktx.migrations import SCHEMA_VERSION, apply_migrations

logger = logging.getLogger("pktx")


class RestoreError(Exception):
    """The archive is unusable or incompatible with the running code."""


def _connect(dsn: str, *, autocommit: bool) -> psycopg.Connection[Any]:
    """Open a dict-row connection to the restore target."""
    return psycopg.connect(
        dsn,
        row_factory=dict_row,  # type: ignore[arg-type]
        autocommit=autocommit,
    )


def read_archive(source: str) -> bytes:
    """Read archive bytes from a local path or an ``s3://bucket/key`` URL."""
    if source.startswith("s3://"):
        import boto3

        bucket, _, key = source[len("s3://") :].partition("/")
        if not key:
            raise RestoreError(f"s3 URL must include a key: {source}")
        obj = boto3.client("s3").get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()  # type: ignore[no-any-return]
    with open(source, "rb") as fh:
        return fh.read()


def unpack(data: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Return ``(manifest, {table: csv_bytes})`` from archive bytes."""
    manifest: dict[str, Any] | None = None
    tables: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            fh = tar.extractfile(member)
            if fh is None:
                continue
            payload = fh.read()
            if member.name == MANIFEST_NAME:
                manifest = json.loads(payload)
            elif member.name.startswith("tables/") and member.name.endswith(".csv"):
                tables[member.name[len("tables/") : -len(".csv")]] = payload
    if manifest is None:
        raise RestoreError("archive has no manifest.json — not a pktx backup")
    return manifest, tables


def restore_into(
    conn: psycopg.Connection[Any],
    manifest: dict[str, Any],
    tables: dict[str, bytes],
) -> dict[str, int]:
    """Truncate and reload every table in the archive. Caller owns the commit."""
    order: list[str] = manifest["table_order"]
    missing = [t for t in order if t not in tables]
    if missing:
        raise RestoreError(f"manifest lists tables with no data: {missing}")

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(", ").join(sql.Identifier(t) for t in order)
            )
        )
        for table in order:
            stmt = sql.SQL("COPY {} FROM STDIN (FORMAT CSV, HEADER)").format(
                sql.Identifier(table)
            )
            with cur.copy(stmt) as copy:
                copy.write(tables[table])

        # COPY inserts explicit ids without advancing SERIAL sequences; without
        # this the next insert collides on the primary key.
        for table in SERIAL_ID_TABLES:
            if table not in order:
                continue
            cur.execute(
                sql.SQL(
                    "SELECT setval(pg_get_serial_sequence({tbl}, 'id'), "
                    "COALESCE((SELECT MAX(id) FROM {ident}), 1), "
                    "(SELECT COUNT(*) FROM {ident}) > 0)"
                ).format(tbl=sql.Literal(table), ident=sql.Identifier(table))
            )

    counts: dict[str, int] = {}
    for table in order:
        row = conn.execute(
            sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))
        ).fetchone()
        counts[table] = int(row["n"] if isinstance(row, dict) else row[0])  # type: ignore[index]
    return counts


def restore_archive(data: bytes, dsn: str, force: bool = False) -> dict[str, int]:
    """Restore archive bytes into the database at ``dsn``.

    Raises:
        RestoreError: archive is malformed, or its schema version differs from
            the running code and ``force`` is not set.
    """
    manifest, tables = unpack(data)
    archive_version = int(manifest["schema_version"])
    if archive_version != SCHEMA_VERSION and not force:
        raise RestoreError(
            f"archive schema v{archive_version} != code schema v{SCHEMA_VERSION}; "
            "check out the matching pktx revision or pass force=True"
        )

    with _connect(dsn, autocommit=True) as migrate_conn:
        apply_migrations(migrate_conn)

    with _connect(dsn, autocommit=False) as conn:
        counts = restore_into(conn, manifest, tables)
        conn.commit()

    logger.info(
        "restore complete rows=%d tables=%d schema_version=%d",
        sum(counts.values()),
        len(counts),
        archive_version,
    )
    return counts
