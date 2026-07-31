#!/usr/bin/env python
"""CLI wrapper around :mod:`pktx.restore_service`.

    uv run python scripts/restore_backup.py <archive> --dsn postgresql://...

``<archive>`` is a local path or an ``s3://bucket/key`` URL. Restoring is
destructive — every table in the archive is truncated first, so point this at a
scratch database unless you mean it.
"""

import argparse
import sys

from pktx.restore_service import RestoreError, read_archive, restore_archive


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore a pktx backup archive")
    parser.add_argument("archive", help="local path or s3://bucket/key")
    parser.add_argument("--dsn", required=True, help="target PostgreSQL DSN")
    parser.add_argument(
        "--force",
        action="store_true",
        help="restore even if the archive schema version differs from the code",
    )
    args = parser.parse_args()

    try:
        counts = restore_archive(read_archive(args.archive), args.dsn, force=args.force)
    except RestoreError as exc:
        print(f"restore failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    for table, n in counts.items():
        print(f"  {table:<16} {n:>8}")
    print(f"restored {sum(counts.values())} rows across {len(counts)} tables")


if __name__ == "__main__":
    main()
