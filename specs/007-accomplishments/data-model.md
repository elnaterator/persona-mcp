# Data Model: Accomplishments Feature (007)

**Phase**: 1 — Design
**Branch**: `feat-007-accomplishments`
**Date**: 2026-02-18

---

## Database Schema (Migration v2 → v3)

File: `backend/src/persona/migrations.py`

```python
def migrate_v2_to_v3(conn: sqlite3.Connection) -> None:
    """Add accomplishment table with STAR fields and tags."""
    conn.executescript("""
        CREATE TABLE accomplishment (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT    NOT NULL,
            situation       TEXT    NOT NULL DEFAULT '',
            task            TEXT    NOT NULL DEFAULT '',
            action          TEXT    NOT NULL DEFAULT '',
            result          TEXT    NOT NULL DEFAULT '',
            accomplishment_date TEXT,
            tags            TEXT    NOT NULL DEFAULT '[]',
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX idx_accomplishment_date
            ON accomplishment(accomplishment_date DESC);
        CREATE INDEX idx_accomplishment_created
            ON accomplishment(created_at DESC);
    """)
```

**Field notes**:
- `title`: Required (NOT NULL, enforced at service layer too). No DEFAULT to force explicit provision.
- `situation`, `task`, `action`, `result`: All optional STAR fields. Empty string default means "not yet filled".
- `accomplishment_date`: Optional ISO 8601 date string (`YYYY-MM-DD`). NULL when not specified.
- `tags`: JSON text array, e.g. `'["leadership","technical"]'`. Normalized (trimmed) at service layer.
- Timestamps: UTC datetime strings managed by SQLite default on insert; service layer updates `updated_at` on every PATCH.

---

## Database Functions

File: `backend/src/persona/database.py` (additions)

```python
def create_accomplishment(conn: DBConnection, data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new accomplishment row and return it."""

def load_accomplishment(conn: DBConnection, acc_id: int) -> dict[str, Any]:
    """Load a single accomplishment by ID. Raises ValueError if not found."""

def load_accomplishments(
    conn: DBConnection,
    tag: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    """List accomplishments ordered by accomplishment_date DESC NULLS LAST,
    created_at DESC. Optionally filter by tag (substring in tags JSON) or
    full-text search query q (case-insensitive substring on title + STAR fields)."""

def update_accomplishment(
    conn: DBConnection, acc_id: int, data: dict[str, Any]
) -> dict[str, Any]:
    """Patch an accomplishment with provided fields. Raises ValueError if not found."""

def delete_accomplishment(conn: DBConnection, acc_id: int) -> dict[str, Any]:
    """Delete an accomplishment. Returns the deleted row. Raises ValueError if not found."""

def load_accomplishment_tags(conn: DBConnection) -> list[str]:
    """Return a sorted unique list of all tags across all accomplishments."""
```

**Sort query pattern**:
```sql
SELECT * FROM accomplishment
ORDER BY
    CASE WHEN accomplishment_date IS NULL THEN 1 ELSE 0 END,
    accomplishment_date DESC,
    created_at DESC
```

**Tag filter pattern** (SQLite JSON via LIKE):
```sql
WHERE tags LIKE '%"' || ? || '"%'
```
(Service layer normalizes the tag before querying.)

---

## Pydantic Models

File: `backend/src/persona/models.py` (additions)

```python
class Accomplishment(BaseModel):
    """A career accomplishment in STAR format."""
    id: int
    title: str
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    accomplishment_date: str | None = None
    tags: list[str] = []
    created_at: str = ""
    updated_at: str = ""


class AccomplishmentSummary(BaseModel):
    """Accomplishment summary for list views (STAR body omitted)."""
    id: int
    title: str
    accomplishment_date: str | None = None
    tags: list[str] = []
    created_at: str = ""
    updated_at: str = ""
```

---

## Service Layer

File: `backend/src/persona/accomplishment_service.py` (new file)

```python
class AccomplishmentService:
    def __init__(self, conn: DBConnection) -> None: ...

    def list_accomplishments(
        self, tag: str | None = None, q: str | None = None
    ) -> list[dict[str, Any]]:
        """Return AccomplishmentSummary dicts, ordered reverse-chronologically."""

    def list_tags(self) -> list[str]:
        """Return sorted unique tag list for autocomplete."""

    def get_accomplishment(self, acc_id: int) -> dict[str, Any]:
        """Return full Accomplishment dict. Raises ValueError if not found."""

    def create_accomplishment(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate and persist a new accomplishment. Raises ValueError if title missing."""

    def update_accomplishment(
        self, acc_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Patch fields. Raises ValueError if not found or title would become empty."""

    def delete_accomplishment(self, acc_id: int) -> dict[str, Any]:
        """Delete. Raises ValueError if not found."""
```

**Validation rules**:
- `title` is required on create; must not be blank.
- `title` cannot be set to blank on update (if provided, must be non-empty after strip).
- Tags are trimmed of whitespace individually and deduplicated before storage.
- `accomplishment_date` must match `YYYY-MM-DD` format if provided; otherwise rejected with a ValueError.

---

## TypeScript Types

File: `frontend/src/types/resume.ts` (additions)

```typescript
export interface Accomplishment {
  id: number
  title: string
  situation: string
  task: string
  action: string
  result: string
  accomplishment_date: string | null
  tags: string[]
  created_at: string
  updated_at: string
}

export interface AccomplishmentSummary {
  id: number
  title: string
  accomplishment_date: string | null
  tags: string[]
  created_at: string
  updated_at: string
}
```

---

## Entity Relationships

```
accomplishment (standalone entity, no FK relationships)
│
├── id                  INTEGER PK
├── title               TEXT (required)
├── situation           TEXT (STAR field)
├── task                TEXT (STAR field)
├── action              TEXT (STAR field)
├── result              TEXT (STAR field)
├── accomplishment_date TEXT ISO-8601 (nullable)
├── tags                TEXT JSON array
├── created_at          TEXT datetime
└── updated_at          TEXT datetime
```

The `accomplishment` table is intentionally standalone — it does not reference `resume_version` because accomplishments are global to the user, not version-specific. This keeps the data model simple and avoids the need to migrate accomplishments when resume versions are deleted.
