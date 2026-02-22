# Data Model: PostgreSQL Migration (009-postgres)

**Date**: 2026-02-20
**Phase**: 1 — Design

This document describes the PostgreSQL schema that replaces the SQLite schema v4. The logical data model (entities, relationships, business rules) is **unchanged**. Only storage types, column defaults, and primary key generation mechanisms change.

---

## Schema Version Tracking (New)

**Entity**: `schema_version`

A new single-row table replacing SQLite's `PRAGMA user_version`. This table is created before any migrations run.

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL DEFAULT 0
);
-- Seed with 0 on first install
INSERT INTO schema_version (version) VALUES (0) ON CONFLICT DO NOTHING;
```

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `version` | INTEGER | NOT NULL | Current schema version integer |

**Business rules**: Always exactly one row. Version is read at startup and incremented atomically with each migration's DDL in the same transaction.

---

## Users

**Entity**: `users`

No logical changes. Column types refined for PostgreSQL.

```sql
CREATE TABLE users (
    id           TEXT PRIMARY KEY,
    email        TEXT,
    display_name TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | TEXT | PRIMARY KEY | Clerk user ID (external string) |
| `email` | TEXT | nullable | May be null for some auth providers |
| `display_name` | TEXT | nullable | Display name from Clerk |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | PostgreSQL TIMESTAMP replaces SQLite TEXT |

**Relationships**: Parent table for `resume_version`, `application`, `accomplishment` via `user_id FK`.

**Identity rule**: TEXT primary key (Clerk-assigned). No auto-increment needed.

---

## Resume Version

**Entity**: `resume_version`

```sql
CREATE TABLE resume_version (
    id          SERIAL PRIMARY KEY,
    user_id     TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label       TEXT        NOT NULL,
    is_default  INTEGER     NOT NULL DEFAULT 0,
    resume_data TEXT        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment; replaces `INTEGER PRIMARY KEY AUTOINCREMENT` |
| `user_id` | TEXT | NOT NULL, FK → users(id) ON DELETE CASCADE | Scopes version to user |
| `label` | TEXT | NOT NULL | Human-readable name for this resume variant |
| `is_default` | INTEGER | NOT NULL, DEFAULT 0 | 1 = default for this user, 0 = not default |
| `resume_data` | TEXT | NOT NULL, DEFAULT '{}' | JSON blob (full resume snapshot) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification time; updated explicitly |

**Indexes**:
```sql
CREATE INDEX idx_resume_version_user ON resume_version(user_id);
CREATE INDEX idx_resume_version_user_default
    ON resume_version(user_id, is_default) WHERE is_default = 1;
CREATE INDEX idx_resume_version_default
    ON resume_version(is_default) WHERE is_default = 1;
```

**Business rules**:
- At most one row per user has `is_default = 1`.
- Deleting the default version auto-promotes the most recently updated remaining version.
- Cannot delete the last remaining version for a user.

---

## Application

**Entity**: `application`

```sql
CREATE TABLE application (
    id                SERIAL PRIMARY KEY,
    user_id           TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company           TEXT    NOT NULL,
    position          TEXT    NOT NULL,
    description       TEXT    NOT NULL DEFAULT '',
    status            TEXT    NOT NULL DEFAULT 'Interested',
    url               TEXT,
    notes             TEXT    NOT NULL DEFAULT '',
    resume_version_id INTEGER REFERENCES resume_version(id) ON DELETE SET NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `user_id` | TEXT | NOT NULL, FK → users(id) ON DELETE CASCADE | |
| `company` | TEXT | NOT NULL | |
| `position` | TEXT | NOT NULL | |
| `description` | TEXT | NOT NULL, DEFAULT '' | |
| `status` | TEXT | NOT NULL, DEFAULT 'Interested' | Enum-like: Interested, Applied, Interviewing, Offer, Rejected, Accepted |
| `url` | TEXT | nullable | Job posting URL |
| `notes` | TEXT | NOT NULL, DEFAULT '' | |
| `resume_version_id` | INTEGER | nullable, FK → resume_version(id) ON DELETE SET NULL | |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

**Indexes**:
```sql
CREATE INDEX idx_application_user    ON application(user_id);
CREATE INDEX idx_application_status  ON application(status);
CREATE INDEX idx_application_updated ON application(updated_at DESC);
```

---

## Application Contact

**Entity**: `application_contact`

```sql
CREATE TABLE application_contact (
    id     SERIAL  PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES application(id) ON DELETE CASCADE,
    name   TEXT    NOT NULL,
    role   TEXT,
    email  TEXT,
    phone  TEXT,
    notes  TEXT    NOT NULL DEFAULT ''
);
```

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | |
| `app_id` | INTEGER | NOT NULL, FK → application(id) ON DELETE CASCADE | |
| `name` | TEXT | NOT NULL | |
| `role` | TEXT | nullable | |
| `email` | TEXT | nullable | |
| `phone` | TEXT | nullable | |
| `notes` | TEXT | NOT NULL, DEFAULT '' | |

**Index**: `CREATE INDEX idx_application_contact_app ON application_contact(app_id);`

---

## Communication

**Entity**: `communication`

```sql
CREATE TABLE communication (
    id           SERIAL  PRIMARY KEY,
    app_id       INTEGER NOT NULL REFERENCES application(id) ON DELETE CASCADE,
    contact_id   INTEGER REFERENCES application_contact(id) ON DELETE SET NULL,
    contact_name TEXT,
    type         TEXT    NOT NULL,
    direction    TEXT    NOT NULL,
    subject      TEXT    NOT NULL DEFAULT '',
    body         TEXT    NOT NULL,
    date         TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'sent',
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
```sql
CREATE INDEX idx_communication_app  ON communication(app_id);
CREATE INDEX idx_communication_date ON communication(date DESC);
```

---

## Accomplishment

**Entity**: `accomplishment`

```sql
CREATE TABLE accomplishment (
    id                  SERIAL    PRIMARY KEY,
    user_id             TEXT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               TEXT      NOT NULL,
    situation           TEXT      NOT NULL DEFAULT '',
    task                TEXT      NOT NULL DEFAULT '',
    action              TEXT      NOT NULL DEFAULT '',
    result              TEXT      NOT NULL DEFAULT '',
    accomplishment_date TEXT,
    tags                TEXT      NOT NULL DEFAULT '[]',
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
```sql
CREATE INDEX idx_accomplishment_user    ON accomplishment(user_id);
CREATE INDEX idx_accomplishment_date    ON accomplishment(accomplishment_date DESC);
CREATE INDEX idx_accomplishment_created ON accomplishment(created_at DESC);
```

**Note on `tags`**: Stored as a TEXT JSON array (`'["tag1","tag2"]'`) for consistency with the existing code. Tag search uses `ILIKE %s` instead of `LIKE ?`. Upgrading to `JSONB` with the `@>` operator is a future enhancement outside this feature's scope.

---

## State Transitions

### Resume Version `is_default` lifecycle

```
[created, is_default=0]
    → set_default()  → [is_default=1]  (all siblings set to 0)
    → delete()       → if was default, most-recently-updated sibling promoted to is_default=1
```

### Application `status` transitions (no enforcement in DB)

```
Interested → Applied → Interviewing → Offer → Accepted
                                    → Rejected
```

---

## Key Changes vs SQLite Schema v4

| Aspect | SQLite v4 | PostgreSQL (this feature) |
|--------|-----------|--------------------------|
| Version tracking | `PRAGMA user_version` | `schema_version` table |
| Primary keys | `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| Timestamp type | `TEXT` (ISO string) | `TIMESTAMP` (native) |
| Timestamp default | `datetime('now')` | `CURRENT_TIMESTAMP` |
| JSON storage | `TEXT DEFAULT '[]'` | `TEXT DEFAULT '[]'` (unchanged) |
| Partial indexes | Supported | Supported (same syntax) |
| Upsert | `ON CONFLICT DO UPDATE` | `ON CONFLICT DO UPDATE` (same) |
| Insert ID retrieval | `cursor.lastrowid` | `RETURNING id` |
