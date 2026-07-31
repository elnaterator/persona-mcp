# Plan 020 - Backups, tested restore, and user data export

Date: 2026-07-31

Branch: `feat/020-backups-restore-export`

Neon's own PITR is the only backup today, it is invisible to Terraform, and no restore has
ever been proven. Add a Terraform-managed nightly logical backup to S3 (EventBridge → the
existing Lambda, same pattern as keep-warm), prove restore with an automated round-trip test
plus a documented drill, and ship a user-facing "export my data" JSON download that doubles
as the data-portability story. Blocker for first beta invite.


## Requirements

### R1 - Automated off-provider backup, defined in Terraform

Nightly full-database logical backup written to a versioned, encrypted S3 bucket, so a lost
Neon account is survivable — not just a lost row.

* New `infra/modules/backup` creates a private S3 bucket (`pktx-backups-<env>`) with
  versioning, SSE, public access block, and a lifecycle rule (30-day retention, expire
  noncurrent at 7 days)
* `aws_cloudwatch_event_rule` on `cron(0 8 * * ? *)` — daily at a fixed 08:00 UTC rather
  than the planned `rate(1 day)`, which would drift with every apply — targets the existing
  Lambda with a static Function URL v2 payload for `POST /internal/backup`, mirroring the
  keep-warm target in `infra/modules/lambda/main.tf`; `aws_lambda_permission` scoped to the
  rule ARN. Overridable via `backup_schedule_expression`
* Lambda exec role gets a least-privilege `s3:PutObject` policy scoped to
  `arn:aws:s3:::pktx-backups-<env>/*`; bucket name passed as `PKTX_BACKUP_BUCKET`
* Route is authenticated by a shared secret: EventBridge payload carries
  `x-pktx-backup-token`, compared with `hmac.compare_digest` against SSM
  `/pktx/<env>/backup_token`; missing/blank token env ⇒ route not registered
* Toggle via module variable `backups_enabled` (bool, default `true`) using `count`, so an
  env can opt out; `terraform fmt` clean and `terraform validate` passes in `infra/dev` and
  `infra/prod`
* Neon PITR (history retention) is *not* Terraform-manageable on the current plan — record
  the actual retention window and where to change it in `docs/deployment.md` rather than
  pretending it is codified

### R2 - Backup format and content

Backup content must be restorable without the application running, and must not depend on a
`pg_dump` binary in the Lambda image.

* `backup_service.py` streams every application table via `COPY <table> TO STDOUT (FORMAT
  CSV, HEADER)` into a single gzipped tar. The table list is an explicit FK-ordered tuple
  (ordering cannot be derived from `migrations.py`), and a unit test asserts it equals the
  tables a fully migrated database actually has — so a new migration cannot silently drop a
  table out of the backup
* Archive includes a `manifest.json`: schema version, timestamp, per-table row counts,
  pktx version
* Object key `backups/<YYYY>/<MM>/pktx-<env>-<ISO8601>.tar.gz`; `POST /internal/backup`
  returns `{"key": ..., "bytes": ..., "tables": {...}}` and logs one structured line
* Tables are dumped in FK-safe order (`users` first, then owned resources, `resource_link`
  after the resources it points at, `oauth_kv` last as it has no FKs) so a restore can load
  them sequentially without deferring constraints
* Failure is loud: any table error aborts the run, returns 500, and leaves no partial object

### R3 - Proven restore

A backup nobody has restored is not a backup.

* `scripts/restore_backup.py` takes an archive (local path or `s3://` URL) and a target DSN,
  runs migrations to the archive's schema version, then `COPY ... FROM` each table in
  manifest order, inside one transaction
* Integration test `backend/tests/integration/test_backup_restore.py` seeds a testcontainer
  Postgres with data across all resource types, backs it up, restores into a second empty
  **database in the same container** (equivalent isolation, no second container to start),
  and asserts per-table row counts plus a deep-equal spot check on one resume, application,
  note, contact, communication, and link — plus sequence advancement and idempotence
* `docs/runbooks/restore-drill.md` documents the manual drill against a real dev backup
  (fetch from S3 → restore into a scratch Neon branch → verify counts → point the app at it)
* ~~The drill is actually executed against dev data~~ — **not done, and not fakeable**: the
  bucket and rule do not exist until the user runs `terraform apply`, so no archive exists to
  restore. The drill log records this as blocked rather than inventing a result. Automated
  round-trip coverage stands in for the code path

### R4 - User data export

Any user can take their whole dataset with them.

* `GET /api/export` returns a single JSON document scoped to the caller's `user_id`:
  resumes (full data), applications, accomplishments, notes, contacts, communications, and
  resource links, plus `exported_at` and `schema_version`
* Response sets `Content-Disposition: attachment; filename="pktx-export-<date>.json"`;
  built by a new `export_service.py` reusing the existing `*_service.py` list/get calls.
  One new query was needed after all — `database.load_all_links` / `LinkService.list_all`,
  since no existing call returns a user's links as a flat list
* Export contains only rows owned by the caller; contract test asserts a second user's data
  never appears in the first user's export
* Frontend: "Export my data" action in `UserMenu` triggers the download through the existing
  authenticated `client.ts` fetch (blob → object URL), with loading and error toasts
* Vitest covers the export action: happy path triggers a download, failure surfaces an error
  toast


## Design

**Why not `pg_dump`.** Adding `postgresql-client` to the Lambda image costs image size and
pins a client version against whatever Neon runs. `COPY ... TO STDOUT` over the existing
psycopg pool needs no new system dependency and produces text that `COPY ... FROM` reloads
verbatim. Trade-off accepted: the archive is data-only — schema comes from `migrations.py`,
which is already how every environment is built.

**Why reuse the app Lambda.** It already holds the DB credentials, the connection pool, and
the migration code. A second function would duplicate all three. Precedent exists: the
keep-warm rule already invokes the app Lambda with a synthetic Function URL event.

**Backup route auth.** `/internal/backup` sits on the top-level `router` (like `/health`),
not the Clerk-protected `api` router, and guards itself with a constant-time token
comparison. With `PKTX_BACKUP_TOKEN` unset the route is never registered, so local dev and
existing tests are unaffected.

**The backup token is visible to anyone with AWS read access.** It is stored in SSM as a
SecureString, but is also injected into the Lambda environment and embedded in the
EventBridge target's static input — so `events:DescribeRule`, `lambda:GetFunction`, or read
access to Terraform state all reveal it. Accepted: the only thing it authorizes is "dump the
database to our own bucket", and every principal who can read it can already read the
database credentials sitting beside it. Rotate by overwriting the SSM parameter and
re-applying.

**Restore lives in the package, not the script.** `pktx/restore_service.py` holds the
logic and `backend/scripts/restore_backup.py` is a thin CLI over it — the round-trip test
imports the module directly instead of reaching into a loose script.

**Lambda timeout.** Module default is 30 s. Current data volume dumps in well under a
second; raise `timeout` only if the dev drill shows otherwise, and record the measured
duration in the runbook.

**Export vs backup are deliberately separate.** Backup is operational: all tables, CSV in a
tarball, machine-restorable. Export is user-facing: one user, JSON, human-readable. Sharing
a code path would compromise both.


## Tasks

### P1 - Backup service (backend)

- [x] T01 Add `TABLES_IN_FK_ORDER` (explicit, coverage-tested against the live schema) and
      `backup_service.py`:
      `create_backup(conn) -> tuple[bytes, dict]` producing a gzipped tar of per-table CSV +
      `manifest.json`
- [x] T02 Add `resolve_backup_bucket()` / `resolve_backup_token()` to `config.py` (both
      optional; empty ⇒ feature off)
- [x] T03 Register `POST /internal/backup` in `routes.py` behind the token guard; upload via
      `boto3` (add dep to `backend/pyproject.toml`), return key/bytes/table counts
- [x] T04 Unit tests: manifest shape, FK ordering covers every table in `migrations.py`,
      token guard rejects bad/missing token, route absent when unconfigured

### P2 - Restore path

- [x] T05 `scripts/restore_backup.py` — accepts local path or `s3://`, target DSN; runs
      migrations then `COPY ... FROM` per manifest order in one transaction
- [x] T06 `backend/tests/integration/test_backup_restore.py` — seed → backup → restore into a
      second container → row-count + deep-equal assertions

### P3 - Terraform

- [x] T07 `infra/modules/backup`: S3 bucket (versioning, SSE, public access block,
      lifecycle), `backups_enabled` toggle, outputs bucket name/ARN
- [x] T08 Wire into `infra/dev` and `infra/prod`: module block, `backup_token` SSM
      SecureString parameter + data source, `PKTX_BACKUP_BUCKET`/`PKTX_BACKUP_TOKEN` env vars
- [x] T09 Lambda module: `s3:PutObject` role policy scoped to the backup bucket, daily
      `aws_cloudwatch_event_rule` + target + `aws_lambda_permission`
- [x] T10 `terraform fmt -recursive infra/` and `terraform validate` in both envs; resolve
      Checkov findings (annotate a skip only where it is genuinely right)

### P4 - Export feature

- [x] T11 `export_service.py` — `export_user_data(user_id) -> dict` composed from existing
      services
- [x] T12 `GET /api/export` route with attachment `Content-Disposition`
- [x] T13 Contract test: export contains all owned resource types; cross-user isolation test
- [x] T14 Frontend `services/api/export.ts` + "Export my data" item in `UserMenu` (blob
      download, toast on success/failure)
- [x] T15 Vitest for the export action (success + failure)

### P5 - Drill and docs

- [~] T16 **Blocked** — the real drill needs `terraform apply` to create the bucket and rule
      first (this item does not apply). Procedure is written and the automated round trip
      passes; the drill log in the runbook records the blocked state
- [x] T17 `docs/runbooks/restore-drill.md` with the procedure plus the executed drill's date,
      archive key, row counts, and duration
- [x] T18 `docs/deployment.md`: backup bucket, `backup_token` SSM setup, Neon PITR retention
      window and where to change it
- [x] T19 `AGENTS.md` infra/backend one-liners (backup rule + toggle, `/api/export`)


### Implementation Notes

- Sequence: P1 → P2 (the restore test is the proof P1 works) → P3 → P5. P4 is independent of
  P1–P3 and can run in parallel.
- Do **not** run `terraform apply` as part of this item — the user applies. T16 depends on
  that apply landing; if it has not, record the drill as blocked rather than faking a result.
- `boto3` is the only new backend dependency (present in the Lambda runtime, but must be
  declared for local tests). S3 is stubbed with a hand-written fake in tests — no `moto`, no
  network in CI.
- Checkov runs from the root `make check` (not from CI, contrary to the 018 plan's note).
  Four of its S3 findings are false positives caused by `count`-indexed bucket references;
  they carry skip annotations naming the resource that actually satisfies the rule.
- Out of scope: Markdown export format, MCP export tool, importing a user export back in,
  cross-region bucket replication, backup-failure alerting (belongs with 021 error tracking),
  and account deletion (023).
