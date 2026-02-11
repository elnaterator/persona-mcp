# Data Model: SQLite Storage

**Feature**: feat-003-sqlite
**Date**: 2026-02-11
**Source**: spec.md Key Entities + research.md decisions

## Entity Relationship Overview

```
┌─────────────┐
│   contact    │  (singleton - max 1 row)
│─────────────│
│ name         │
│ email        │
│ phone        │
│ location     │
│ linkedin     │
│ website      │
│ github       │
└─────────────┘

┌─────────────┐
│   summary    │  (singleton - max 1 row)
│─────────────│
│ text         │
└─────────────┘

┌──────────────┐
│  experience  │  (ordered collection, 0..N rows)
│──────────────│
│ id (PK)      │
│ title *      │
│ company *    │
│ start_date   │
│ end_date     │
│ location     │
│ highlights   │  ← JSON text: ["item1", "item2"]
│ position     │  ← integer for ordering (0 = newest)
└──────────────┘

┌──────────────┐
│  education   │  (ordered collection, 0..N rows)
│──────────────│
│ id (PK)      │
│ institution *│
│ degree *     │
│ field        │
│ start_date   │
│ end_date     │
│ honors       │
│ position     │  ← integer for ordering (0 = newest)
└──────────────┘

┌──────────────┐
│    skill     │  (collection, 0..N rows, unique by name)
│──────────────│
│ id (PK)      │
│ name * (UQ)  │
│ category     │  ← defaults to "Other"
└──────────────┘

(* = required field, PK = primary key, UQ = unique constraint)
```

## Schema DDL (Migration v0 → v1)

```sql
CREATE TABLE IF NOT EXISTS contact (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT,
    email TEXT,
    phone TEXT,
    location TEXT,
    linkedin TEXT,
    website TEXT,
    github TEXT
);

CREATE TABLE IF NOT EXISTS summary (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    text TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    location TEXT,
    highlights TEXT NOT NULL DEFAULT '[]',
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS education (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT NOT NULL,
    degree TEXT NOT NULL,
    field TEXT,
    start_date TEXT,
    end_date TEXT,
    honors TEXT,
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'Other'
);
```

## Design Decisions

### Singleton Tables (contact, summary)

- `CHECK (id = 1)` constraint ensures at most one row per table.
- First write uses `INSERT OR REPLACE` semantics.
- Empty state = no row (not a row with all NULLs). Read returns default Pydantic model when no row exists.

### Ordering (experience, education)

- `position` column stores explicit ordering (0 = first/newest).
- When a new entry is added (prepended), existing positions are incremented and the new entry gets position 0.
- When an entry is removed, positions are compacted.
- This matches the spec requirement: "newest first" ordering.

### Highlights as JSON

- `highlights` column stores a JSON array as TEXT: `'["Led team of 5", "Shipped v2.0"]'`
- Serialized via `json.dumps()`, deserialized via `json.loads()`.
- Default value is `'[]'` (empty JSON array).
- Never queried individually — always read/written as a unit with the parent experience entry.

### Skills Uniqueness

- `UNIQUE` constraint on `name` column enforces FR-005 (duplicate detection).
- Duplicate check is case-sensitive at the DB level; application layer performs case-insensitive comparison before insert (matching current behavior).
- No explicit ordering — skills are grouped by category on read.

### No Foreign Keys Between Tables

- Resume entities are independent top-level collections, not related to each other.
- No cross-table references needed.

## Pydantic ↔ SQLite Mapping

| Pydantic Model | SQLite Table | Notes |
|----------------|--------------|-------|
| `ContactInfo` | `contact` | All fields nullable except enforced by Pydantic |
| `str` (summary) | `summary` | Single `text` column |
| `WorkExperience` | `experience` | `highlights: list[str]` → JSON TEXT column |
| `Education` | `education` | Direct field mapping |
| `Skill` | `skill` | `category` defaults to "Other" via both Pydantic validator and DB default |
| `Resume` | All tables | Aggregate — assembled by reading all tables |

## Schema Version Tracking

- Uses SQLite's `PRAGMA user_version` (integer stored in file header).
- Version 0 = empty/new database (no tables).
- Version 1 = initial schema (all tables above).
- Future versions increment sequentially.
- Checked on every startup; migrations applied automatically.
