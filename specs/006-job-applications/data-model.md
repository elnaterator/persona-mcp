# Data Model: Job Application Management (rev 3)

**Date**: 2026-02-17
**Feature**: 006-job-applications

## Entities

### ResumeVersion

A complete, independent resume. Replaces the old singleton resume tables.

| Column      | Type    | Constraints                          | Notes                                           |
|-------------|---------|--------------------------------------|-------------------------------------------------|
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT            |                                                 |
| label       | TEXT    | NOT NULL                             | User-chosen label (e.g., "Default Resume")      |
| is_default  | INTEGER | NOT NULL DEFAULT 0                   | Boolean (0/1). Exactly one row has is_default=1  |
| resume_data | TEXT    | NOT NULL DEFAULT '{}'                | JSON blob: full Resume model (contact, summary, experience, education, skills) |
| created_at  | TEXT    | NOT NULL DEFAULT (datetime('now'))   | ISO 8601 UTC                                    |
| updated_at  | TEXT    | NOT NULL DEFAULT (datetime('now'))   | ISO 8601 UTC                                    |

**Invariants**:
- Exactly one row has `is_default = 1` at all times (enforced in application logic)
- Cannot delete the default version if it's the only version
- When setting a new default, the old default is unset in the same transaction
- `resume_data` contains a serialized `Resume` model: `{"contact": {...}, "summary": "...", "experience": [...], "education": [...], "skills": [...]}`

### Application

| Column            | Type    | Constraints                          | Notes                                           |
|-------------------|---------|--------------------------------------|-------------------------------------------------|
| id                | INTEGER | PRIMARY KEY AUTOINCREMENT            |                                                 |
| company           | TEXT    | NOT NULL                             | Company name                                    |
| position          | TEXT    | NOT NULL                             | Position title                                  |
| description       | TEXT    | NOT NULL DEFAULT ''                  | Job description (up to 50,000 chars)            |
| status            | TEXT    | NOT NULL DEFAULT 'Interested'        | One of: Interested, Applied, Phone Screen, Interview, Offer, Accepted, Rejected, Withdrawn |
| url               | TEXT    |                                      | Job posting URL                                 |
| notes             | TEXT    | NOT NULL DEFAULT ''                  | Free-text notes                                 |
| resume_version_id | INTEGER | REFERENCES resume_version(id) ON DELETE SET NULL | Optional FK to associated resume version |
| created_at        | TEXT    | NOT NULL DEFAULT (datetime('now'))   | ISO 8601 UTC                                    |
| updated_at        | TEXT    | NOT NULL DEFAULT (datetime('now'))   | ISO 8601 UTC                                    |

### ApplicationContact

| Column | Type    | Constraints                          | Notes                |
|--------|---------|--------------------------------------|----------------------|
| id     | INTEGER | PRIMARY KEY AUTOINCREMENT            |                      |
| app_id | INTEGER | NOT NULL REFERENCES application(id) ON DELETE CASCADE | Parent application |
| name   | TEXT    | NOT NULL                             | Contact's full name  |
| role   | TEXT    |                                      | Role/title           |
| email  | TEXT    |                                      | Email address        |
| phone  | TEXT    |                                      | Phone number         |
| notes  | TEXT    | NOT NULL DEFAULT ''                  | Notes about contact  |

### Communication

| Column       | Type    | Constraints                          | Notes                                           |
|--------------|---------|--------------------------------------|-------------------------------------------------|
| id           | INTEGER | PRIMARY KEY AUTOINCREMENT            |                                                 |
| app_id       | INTEGER | NOT NULL REFERENCES application(id) ON DELETE CASCADE | Parent application |
| contact_id   | INTEGER | REFERENCES application_contact(id) ON DELETE SET NULL | Optional contact ref |
| contact_name | TEXT    |                                      | Denormalized: populated from contact at creation, retained after contact deletion |
| type         | TEXT    | NOT NULL                             | email, phone, interview_note, other             |
| direction    | TEXT    | NOT NULL                             | sent, received                                  |
| subject      | TEXT    | NOT NULL DEFAULT ''                  | Subject line                                    |
| body         | TEXT    | NOT NULL                             | Full content                                    |
| date         | TEXT    | NOT NULL                             | ISO 8601 date                                   |
| status       | TEXT    | NOT NULL DEFAULT 'sent'              | draft, ready, sent, archived                    |
| created_at   | TEXT    | NOT NULL DEFAULT (datetime('now'))   | ISO 8601 UTC                                    |

## Relationships

```
ResumeVersion 1──┐
                  │ 0..* (optional FK on Application)
Application ──────┘
    │
    ├── 0..* ApplicationContact
    │         │
    └── 0..* Communication ──── 0..1 ApplicationContact (optional)
```

- Application → ResumeVersion: optional many-to-one (resume_version_id FK, ON DELETE SET NULL)
- Application → ApplicationContact: one-to-many (ON DELETE CASCADE)
- Application → Communication: one-to-many (ON DELETE CASCADE)
- Communication → ApplicationContact: optional (ON DELETE SET NULL)

## Migration: v1 → v2

```sql
-- Step 1: Create new tables
CREATE TABLE resume_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0,
    resume_data TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    position TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Interested',
    url TEXT,
    notes TEXT NOT NULL DEFAULT '',
    resume_version_id INTEGER REFERENCES resume_version(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE application_contact (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL REFERENCES application(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT,
    email TEXT,
    phone TEXT,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE communication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL REFERENCES application(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES application_contact(id) ON DELETE SET NULL,
    contact_name TEXT,
    type TEXT NOT NULL,
    direction TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'sent',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Step 2: Migrate existing resume data into default resume version
-- (done in Python: read from old tables, serialize to JSON, insert as version 1)

-- Step 3: Drop old singleton tables
DROP TABLE IF EXISTS contact;
DROP TABLE IF EXISTS summary;
DROP TABLE IF EXISTS experience;
DROP TABLE IF EXISTS education;
DROP TABLE IF EXISTS skill;
```

**Migration logic (Python)**: Read data from old contact, summary, experience, education, skill tables → build a Resume model → serialize to JSON → INSERT into resume_version with label="Default Resume", is_default=1 → DROP old tables. If old tables are empty, create an empty default resume version.

## Indexes

```sql
CREATE INDEX idx_application_status ON application(status);
CREATE INDEX idx_application_updated ON application(updated_at DESC);
CREATE INDEX idx_application_contact_app ON application_contact(app_id);
CREATE INDEX idx_communication_app ON communication(app_id);
CREATE INDEX idx_communication_date ON communication(date DESC);
CREATE INDEX idx_resume_version_default ON resume_version(is_default) WHERE is_default = 1;
```
