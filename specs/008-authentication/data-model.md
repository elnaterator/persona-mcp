# Data Model: Authentication & Multi-user Support (rev 2)

**Date**: 2026-02-19
**Feature**: 008-authentication

This document outlines the changes to the data model to support multiple users via Clerk authentication. Schema advances from **v3 → v4**.

> **Rev 2 change**: Added a dedicated `users` table as the SQLite foreign-key anchor for all owned tables, replacing the previous "virtual/external user" approach (rev 1). All owned tables reference `users(id)` with `ON DELETE CASCADE` to enable atomic hard-deletion.

## Entities

### users (New)

Local SQLite mirror of the Clerk identity. Acts as the FK anchor for all user-owned data. Row is upserted on first successful sign-in; hard-deleted (with cascade) on `user.deleted` webhook.

| Column       | Type    | Constraints                              | Notes                                      |
|--------------|---------|------------------------------------------|--------------------------------------------|
| id           | TEXT    | PRIMARY KEY                              | Clerk `sub` claim (e.g., `user_2S...`)     |
| email        | TEXT    |                                          | From Clerk; may be NULL for social-only    |
| display_name | TEXT    |                                          | From Clerk profile                         |
| created_at   | TEXT    | NOT NULL DEFAULT (datetime('now'))       | ISO 8601 UTC                               |

### resume_version (Updated)

`user_id` column added; now references `users(id)` with `ON DELETE CASCADE`.

| Column      | Type    | Constraints                                                        | Notes                                           |
|-------------|---------|--------------------------------------------------------------------|-------------------------------------------------|
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT                                          |                                                 |
| user_id     | TEXT    | NOT NULL REFERENCES users(id) ON DELETE CASCADE                    | Clerk User ID — FK to users table               |
| label       | TEXT    | NOT NULL                                                           | User-chosen label (e.g., "Default Resume")      |
| is_default  | INTEGER | NOT NULL DEFAULT 0                                                 | Boolean (0/1). Exactly one row per user has is_default=1 |
| resume_data | TEXT    | NOT NULL DEFAULT '{}'                                              | JSON blob: full Resume model                    |
| created_at  | TEXT    | NOT NULL DEFAULT (datetime('now'))                                 | ISO 8601 UTC                                    |
| updated_at  | TEXT    | NOT NULL DEFAULT (datetime('now'))                                 | ISO 8601 UTC                                    |

**Invariants (Multi-user)**:
- Exactly one row has `is_default = 1` **per `user_id`**.
- All queries MUST filter by `user_id`.

### application (Updated)

`user_id` column added; now references `users(id)` with `ON DELETE CASCADE`.

| Column            | Type    | Constraints                                                  | Notes                                           |
|-------------------|---------|--------------------------------------------------------------|-------------------------------------------------|
| id                | INTEGER | PRIMARY KEY AUTOINCREMENT                                    |                                                 |
| user_id           | TEXT    | NOT NULL REFERENCES users(id) ON DELETE CASCADE              | Clerk User ID — FK to users table               |
| company           | TEXT    | NOT NULL                                                     |                                                 |
| position          | TEXT    | NOT NULL                                                     |                                                 |
| description       | TEXT    | NOT NULL DEFAULT ''                                          |                                                 |
| status            | TEXT    | NOT NULL DEFAULT 'Interested'                                |                                                 |
| url               | TEXT    |                                                              | Job posting URL                                 |
| notes             | TEXT    | NOT NULL DEFAULT ''                                          |                                                 |
| resume_version_id | INTEGER | REFERENCES resume_version(id) ON DELETE SET NULL             | Associated resume version (same user enforced by app logic) |
| created_at        | TEXT    | NOT NULL DEFAULT (datetime('now'))                           | ISO 8601 UTC                                    |
| updated_at        | TEXT    | NOT NULL DEFAULT (datetime('now'))                           | ISO 8601 UTC                                    |

**Invariants (Multi-user)**:
- All queries MUST filter by `user_id`.
- Cross-user `resume_version_id` association is forbidden by application logic.

### accomplishment (Updated)

`user_id` column added; now references `users(id)` with `ON DELETE CASCADE`.

| Column               | Type    | Constraints                                              | Notes                   |
|----------------------|---------|----------------------------------------------------------|-------------------------|
| id                   | INTEGER | PRIMARY KEY AUTOINCREMENT                                |                         |
| user_id              | TEXT    | NOT NULL REFERENCES users(id) ON DELETE CASCADE          | Clerk User ID           |
| title                | TEXT    | NOT NULL                                                 |                         |
| situation            | TEXT    | NOT NULL DEFAULT ''                                      |                         |
| task                 | TEXT    | NOT NULL DEFAULT ''                                      |                         |
| action               | TEXT    | NOT NULL DEFAULT ''                                      |                         |
| result               | TEXT    | NOT NULL DEFAULT ''                                      |                         |
| accomplishment_date  | TEXT    |                                                          | ISO 8601 date or NULL   |
| tags                 | TEXT    | NOT NULL DEFAULT '[]'                                    | JSON array              |
| created_at           | TEXT    | NOT NULL DEFAULT (datetime('now'))                       |                         |
| updated_at           | TEXT    | NOT NULL DEFAULT (datetime('now'))                       |                         |

### application_contact, communication (Unchanged schema)

These tables are owned transitively via `application(id)` with `ON DELETE CASCADE`, so cascade deletion through `users → application → application_contact / communication` is already correct.

## Relationships

```
users (local, Clerk sub) 1 ──┬── 0..* resume_version   (user_id FK, ON DELETE CASCADE)
                              ├── 0..* application       (user_id FK, ON DELETE CASCADE)
                              │         └── 0..* application_contact (app_id FK, CASCADE)
                              │         └── 0..* communication       (app_id FK, CASCADE)
                              └── 0..* accomplishment    (user_id FK, ON DELETE CASCADE)
```

- Data isolation is enforced at the query level: `WHERE user_id = :current_user_id`.
- Cascade deletion of all user data is triggered by the `user.deleted` Clerk webhook → `DELETE FROM users WHERE id = :clerk_sub`.

## Migration: v3 → v4

> **Note**: Schema v3 introduced the `accomplishment` table (feature 007). This authentication migration is v4.

SQLite does not support adding `NOT NULL` columns (with FK references) to existing tables via `ALTER TABLE`. The migration recreates owned tables:

1. Create `users` table.
2. Recreate `resume_version`, `application`, and `accomplishment` with `user_id` column and FK reference.
3. Copy existing data, assigning a placeholder `user_id` of `'legacy'` for pre-auth rows (single-user era).
4. Drop old tables, rename new ones.
5. Recreate indexes.

```sql
-- Step 1: users table
CREATE TABLE users (
    id           TEXT PRIMARY KEY,
    email        TEXT,
    display_name TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Insert placeholder for pre-existing data
INSERT INTO users (id) VALUES ('legacy');

-- Step 2a: resume_version
CREATE TABLE resume_version_v4 (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label        TEXT    NOT NULL,
    is_default   INTEGER NOT NULL DEFAULT 0,
    resume_data  TEXT    NOT NULL DEFAULT '{}',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
INSERT INTO resume_version_v4 SELECT id, 'legacy', label, is_default, resume_data, created_at, updated_at FROM resume_version;
DROP TABLE resume_version;
ALTER TABLE resume_version_v4 RENAME TO resume_version;

-- Step 2b: application
CREATE TABLE application_v4 (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company           TEXT    NOT NULL,
    position          TEXT    NOT NULL,
    description       TEXT    NOT NULL DEFAULT '',
    status            TEXT    NOT NULL DEFAULT 'Interested',
    url               TEXT,
    notes             TEXT    NOT NULL DEFAULT '',
    resume_version_id INTEGER REFERENCES resume_version(id) ON DELETE SET NULL,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);
INSERT INTO application_v4 SELECT id, 'legacy', company, position, description, status, url, notes, resume_version_id, created_at, updated_at FROM application;
DROP TABLE application;
ALTER TABLE application_v4 RENAME TO application;

-- Step 2c: accomplishment
CREATE TABLE accomplishment_v4 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              TEXT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title                TEXT    NOT NULL,
    situation            TEXT    NOT NULL DEFAULT '',
    task                 TEXT    NOT NULL DEFAULT '',
    action               TEXT    NOT NULL DEFAULT '',
    result               TEXT    NOT NULL DEFAULT '',
    accomplishment_date  TEXT,
    tags                 TEXT    NOT NULL DEFAULT '[]',
    created_at           TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT    NOT NULL DEFAULT (datetime('now'))
);
INSERT INTO accomplishment_v4 SELECT id, 'legacy', title, situation, task, action, result, accomplishment_date, tags, created_at, updated_at FROM accomplishment;
DROP TABLE accomplishment;
ALTER TABLE accomplishment_v4 RENAME TO accomplishment;
```

## Indexes

New indexes to support efficient user-scoped lookups (recreated after table rename):

```sql
CREATE INDEX idx_resume_version_user ON resume_version(user_id);
CREATE INDEX idx_resume_version_user_default ON resume_version(user_id, is_default) WHERE is_default = 1;
CREATE INDEX idx_application_user ON application(user_id);
CREATE INDEX idx_accomplishment_user ON accomplishment(user_id);
```

Existing indexes on `status`, `updated_at`, `date`, etc. are recreated as part of the migration.
