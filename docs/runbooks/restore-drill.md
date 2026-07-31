# Runbook — Restore Drill

Backups that have never been restored are a guess. This drill restores a real archive
from S3 into a scratch database and verifies the data came back. Run it after any change
to `backup_service.py`, `restore_service.py`, or `migrations.py`, and at least once per
quarter otherwise.

Budget: ~15 minutes.

## Preconditions

- `terraform apply` has run for the environment with `backups_enabled = true`
- `/pktx/{env}/backup_token` is set to a real value in SSM
- At least one archive exists under `s3://pktx-backups-{env}/backups/`
- Your AWS credentials can read that bucket

## Procedure

**1. Pick an archive.**

```bash
ENV=dev
aws s3 ls "s3://pktx-backups-${ENV}/backups/" --recursive | tail -5
KEY=backups/2026/07/pktx-dev-20260731T080000Z.tar.gz   # newest from the listing
```

**2. Fetch it and read the manifest** — this alone catches a truncated or empty dump.

```bash
aws s3 cp "s3://pktx-backups-${ENV}/${KEY}" /tmp/pktx-backup.tar.gz
tar -xzOf /tmp/pktx-backup.tar.gz manifest.json | jq .
```

Expect `schema_version` matching the deployed code and non-zero counts for the tables you
know have data.

**3. Create a scratch target.** Use a Neon branch (fastest) or a local container.

```bash
# Neon: console → project → Branches → New branch (name it restore-drill).
# Copy its connection string.
TARGET_DSN='postgresql://...restore-drill...?sslmode=require'

# Or locally:
docker run -d --name pktx-restore -e POSTGRES_PASSWORD=pw -p 5433:5432 postgres:16-alpine
TARGET_DSN='postgresql://postgres:pw@localhost:5433/postgres'
```

**4. Restore.** The script migrates the target, truncates, and reloads inside one
transaction. It refuses an archive whose schema version differs from the checked-out code.

```bash
cd backend
uv run python scripts/restore_backup.py /tmp/pktx-backup.tar.gz --dsn "$TARGET_DSN"
```

**5. Verify.** Row counts printed by the script must match the manifest. Then spot-check
content and confirm sequences advanced (the classic post-restore failure is a duplicate-key
error on the first insert):

```bash
psql "$TARGET_DSN" -c "SELECT count(*) FROM accomplishment;" \
                   -c "SELECT title FROM note ORDER BY updated_at DESC LIMIT 3;" \
                   -c "SELECT last_value FROM note_id_seq;"
```

**6. Run the app against it** — the real proof is the UI loading data:

```bash
PKTX_DB_URL="$TARGET_DSN" make run-local   # then open the app and sign in
```

**7. Clean up.** Delete the Neon branch or `docker rm -f pktx-restore`, and
`rm /tmp/pktx-backup.tar.gz`. Never leave a scratch branch holding real user data.

## Automated coverage

`backend/tests/integration/test_backup_restore.py` runs this same path on every CI run:
seed → `create_backup` → `restore_archive` into a separate database → assert row counts,
field-for-field equality across all six resource types, sequence advancement, and
idempotence. That test proves the *code*; this drill proves the *deployment* — the bucket,
the credentials, and the archive that actually exists in S3.

## Drill log

Newest first. Record every run, including failures — a failed drill is the most valuable
entry in this file.

| Date | Env | Archive key | Rows restored | Duration | Result |
|------|-----|-------------|---------------|----------|--------|
| 2026-07-31 | — | — | — | — | **Not yet run.** Blocked on the first `terraform apply` that creates the backup bucket and EventBridge rule; no archive exists in S3 yet. Code path verified by `test_backup_restore.py` (round trip green). |
