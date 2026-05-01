# Data Model: Improved Tags Handling

**Feature**: 015-tags-handling  
**Date**: 2026-04-23

---

## No Schema Changes

Tags remain stored as JSON arrays of lowercase strings in the `accomplishment.tags` and `note.tags` columns. No new tables or columns are required.

---

## Tag (Value Object)

Tags are not first-class entities — they are values within parent records.

| Property    | Type     | Constraints                                         |
|-------------|----------|-----------------------------------------------------|
| value       | string   | Non-empty; lowercase; trimmed; max 50 characters    |

**Normalization rules** (applied at commit time, both frontend and backend):
1. Trim leading/trailing whitespace
2. Convert to lowercase
3. Reject if empty after trimming
4. Deduplicate within a record (case-insensitive, since all are lowercase after step 2)
5. Reject if length > 50 characters (NoteService already enforces; AccomplishmentService must be updated)

---

## Updated Service Signatures

### AccomplishmentService

```python
# Before
def list_accomplishments(self, tag: str | None, ...) -> list[dict]

# After
def list_accomplishments(self, tags: list[str] | None, ...) -> list[dict]
```

```python
# _normalize_tags — add lowercase (currently missing for accomplishments)
def _normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
```

### NoteService

```python
# Before
def list_notes(self, tag: str | None, ...) -> list[dict]

# After
def list_notes(self, tags: list[str] | None, ...) -> list[dict]
```

---

## Updated Database Function Signatures

### `load_accomplishments` and `load_notes`

```python
# Before
def load_accomplishments(conn, tag: str | None, ...) -> list[dict]

# After
def load_accomplishments(conn, tags: list[str] | None, ...) -> list[dict]
```

**AND logic query construction**:
```python
if tags:
    for tag in tags:
        conditions.append("tags ILIKE %s")
        params.append(f'%"{tag}"%')
```

Each tag produces one ILIKE condition; all conditions joined with AND via the existing `WHERE` builder.

---

## Frontend Tag State

Tags in forms are managed as `string[]` (array of committed chips). The `TagInput` component receives and emits `string[]`.

| State field      | Type       | Description                                      |
|------------------|------------|--------------------------------------------------|
| committed tags   | string[]   | Chips already committed; sent to API on save     |
| input text       | string     | Text currently being typed (not yet committed)   |
| dropdown open    | boolean    | Whether autocomplete dropdown is visible         |
| available tags   | string[]   | Pool from API (listAccomplishmentTags / listNoteTags) |

---

## API Parameter Changes

| Endpoint                    | Before              | After                                      |
|-----------------------------|---------------------|--------------------------------------------|
| `GET /api/accomplishments`  | `?tag=leadership`   | `?tag=leadership&tag=technical` (repeated) |
| `GET /api/notes`            | `?tag=leadership`   | `?tag=leadership&tag=technical` (repeated) |

FastAPI route parameter type change:
```python
# Before
tag: str | None = None

# After
tag: list[str] | None = Query(default=None)
```
