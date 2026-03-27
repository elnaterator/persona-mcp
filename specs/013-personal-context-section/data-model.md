# Data Model: Personal Context Notes (013)

**Phase**: 1 — Design
**Branch**: `013-personal-context-section`
**Date**: 2026-03-26

---

## Database Schema (Migration v5 → v6)

File: `backend/src/persona/migrations.py`

```python
def migrate_v5_to_v6(conn) -> None:
    """Add note table for personal context notes."""
    conn.execute("""
        CREATE TABLE note (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT NOT NULL,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL DEFAULT '',
            tags        TEXT NOT NULL DEFAULT '[]',
            created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_note_user FOREIGN KEY (user_id)
                REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.execute(
        "CREATE INDEX idx_note_user ON note(user_id)"
    )
    conn.execute(
        "CREATE INDEX idx_note_updated ON note(updated_at DESC)"
    )
```

**Field notes**:
- `title`: Required (NOT NULL, enforced at service layer too). Max 255 characters (service layer).
- `content`: Optional. Empty string default means "not yet filled". Max 10,000 characters (service layer).
- `tags`: JSON text array, e.g. `'["project","python"]'`. Normalized (trimmed + lowercased) at service layer. Each tag max 50 characters (service layer).
- `user_id`: Required FK to `users(id)`. Cascade delete ensures notes are removed when user is deleted.
- Timestamps: UTC datetime managed by PostgreSQL CURRENT_TIMESTAMP default; service layer updates `updated_at` on every PATCH.

---

## Database Functions

File: `backend/src/persona/database.py` (additions)

```python
def create_note(
    conn: DBConnection,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Insert a new note row and return it."""

def load_note(
    conn: DBConnection,
    note_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Load a single note by ID. Raises ValueError if not found."""

def load_notes(
    conn: DBConnection,
    tag: str | None = None,
    q: str | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """List notes as summaries ordered by updated_at DESC.
    Optionally filter by tag (exact match in tags JSON) or
    keyword search q (case-insensitive substring on title + content, AND logic for multiple words)."""

def update_note(
    conn: DBConnection,
    note_id: int,
    data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    """Patch a note with provided fields. Raises ValueError if not found."""

def delete_note(
    conn: DBConnection,
    note_id: int,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Delete a note. Returns the deleted row. Raises ValueError if not found."""

def load_note_tags(
    conn: DBConnection,
    user_id: str | None = None,
) -> list[str]:
    """Return a sorted unique list of all tags across all notes for a user."""
```

**Sort query**:
```sql
SELECT id, title, tags, created_at, updated_at
FROM note
WHERE user_id = %s
ORDER BY updated_at DESC
```

**Tag filter pattern** (PostgreSQL ILIKE):
```sql
AND tags ILIKE %s
-- parameter: f'%"{tag}"%'
```

**Keyword search pattern** (multi-word AND):
```sql
-- For q="python deployment" (split by whitespace, each word must match)
AND (title ILIKE '%python%' OR content ILIKE '%python%')
AND (title ILIKE '%deployment%' OR content ILIKE '%deployment%')
```

**Row-to-dict helpers**:
```python
def _row_to_note(row) -> dict[str, Any]:
    """Full note with content."""
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "content": row["content"],
        "tags": json.loads(row["tags"]),
        "created_at": _dt(row["created_at"]),
        "updated_at": _dt(row["updated_at"]),
    }

def _row_to_note_summary(row) -> dict[str, Any]:
    """Summary for list view (content omitted)."""
    return {
        "id": row["id"],
        "title": row["title"],
        "tags": json.loads(row["tags"]),
        "created_at": _dt(row["created_at"]),
        "updated_at": _dt(row["updated_at"]),
    }
```

---

## Pydantic Models

File: `backend/src/persona/models.py` (additions)

```python
class Note(BaseModel):
    """A personal context note."""
    id: int
    title: str
    content: str = ""
    tags: list[str] = []
    created_at: str = ""
    updated_at: str = ""


class NoteSummary(BaseModel):
    """Note summary for list views (content omitted)."""
    id: int
    title: str
    tags: list[str] = []
    created_at: str = ""
    updated_at: str = ""
```

---

## Service Layer

File: `backend/src/persona/note_service.py` (new file)

```python
class NoteService:
    """Note CRUD operations with constructor-injected DB connection."""

    def __init__(self, conn: DBConnection) -> None: ...

    def list_notes(
        self, tag: str | None = None, q: str | None = None, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Return NoteSummary dicts, ordered by updated_at DESC."""

    def list_tags(self, user_id: str | None = None) -> list[str]:
        """Return sorted unique tag list for autocomplete."""

    def get_note(self, note_id: int, user_id: str | None = None) -> dict[str, Any]:
        """Return full Note dict. Raises ValueError if not found."""

    def create_note(
        self, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Validate and persist a new note.

        Raises:
            ValueError: If title is missing/blank, or length limits exceeded.
        """

    def update_note(
        self, note_id: int, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, Any]:
        """Patch fields. Raises ValueError if not found or title would become empty.

        Only fields present in data are updated. Absent keys are left unchanged.
        """

    def delete_note(
        self, note_id: int, user_id: str | None = None
    ) -> dict[str, Any]:
        """Delete. Raises ValueError if not found."""
```

**Validation rules**:
- `title` is required on create; must not be blank after `.strip()`.
- `title` cannot be set to blank on update (if provided, must be non-empty after strip).
- `title` max length: 255 characters. Raises `ValueError("Title must not exceed 255 characters")`.
- `content` max length: 10,000 characters. Raises `ValueError("Content must not exceed 10000 characters")`.
- Tags: Trimmed, lowercased, and deduplicated via `_normalize_tags()`.
- Each tag max length: 50 characters. Raises `ValueError("Tag must not exceed 50 characters: '{tag}'")`.
- `content` is optional; defaults to empty string if not provided.

**Tag normalization** (differs from accomplishments by adding lowercase):
```python
def _normalize_tags(tags: list[str]) -> list[str]:
    """Trim whitespace, lowercase, and deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
```

---

## TypeScript Types

File: `frontend/src/types/resume.ts` (additions)

```typescript
export interface Note {
  id: number
  title: string
  content: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface NoteSummary {
  id: number
  title: string
  tags: string[]
  created_at: string
  updated_at: string
}
```

---

## Entity Relationships

```
note (standalone entity, FK to users only)
│
├── id          SERIAL PK
├── user_id     TEXT FK → users(id) ON DELETE CASCADE
├── title       TEXT (required, max 255)
├── content     TEXT (optional, max 10,000)
├── tags        TEXT JSON array (each tag max 50, lowercased)
├── created_at  TIMESTAMP
└── updated_at  TIMESTAMP
```

The `note` table is standalone (like `accomplishment`) — it does not reference `resume_version` or `application`. Notes are global to the user, not tied to a specific resume version or job application.
