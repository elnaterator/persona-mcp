# Backend API Contracts: Improved Tags Handling

**Feature**: 015-tags-handling  
**Date**: 2026-04-23

---

## Changed Endpoints

### GET /api/accomplishments

**Change**: `tag` query parameter now accepts multiple values (AND logic).

**Before**:
```
GET /api/accomplishments?tag=leadership
→ Returns accomplishments tagged with "leadership"
```

**After**:
```
GET /api/accomplishments?tag=leadership
→ Returns accomplishments tagged with "leadership" (unchanged single-tag behavior)

GET /api/accomplishments?tag=leadership&tag=technical
→ Returns accomplishments tagged with BOTH "leadership" AND "technical"

GET /api/accomplishments
→ Returns all accomplishments (unchanged)
```

**FastAPI signature**:
```python
def list_accomplishments(
    tag: list[str] | None = Query(default=None),
    q: str | None = None,
    current_user: UserContext | None = Depends(_user_dep),
) -> list[dict[str, Any]]:
    uid = current_user.id if current_user is not None else None
    return acc_service.list_accomplishments(tags=tag, q=q, user_id=uid)
```

**Response shape**: Unchanged (`AccomplishmentSummary[]`).

---

### GET /api/notes

**Change**: Same as accomplishments — `tag` accepts multiple values with AND logic.

**Before**:
```
GET /api/notes?tag=career
→ Returns notes tagged with "career"
```

**After**:
```
GET /api/notes?tag=career&tag=personal
→ Returns notes tagged with BOTH "career" AND "personal"
```

**FastAPI signature**:
```python
def list_notes(
    tag: list[str] | None = Query(default=None),
    q: str | None = None,
    current_user: UserContext | None = Depends(_user_dep),
) -> list[dict[str, Any]]:
    uid = current_user.id if current_user is not None else None
    return note_service.list_notes(tags=tag, q=q, user_id=uid)
```

---

## Unchanged Endpoints

| Endpoint                         | Change |
|----------------------------------|--------|
| `GET /api/accomplishments/tags`  | None   |
| `GET /api/accomplishments/{id}`  | None   |
| `POST /api/accomplishments`      | None (tags already normalized server-side; lowercase normalization added) |
| `PATCH /api/accomplishments/{id}`| None (same as above) |
| `DELETE /api/accomplishments/{id}` | None |
| `GET /api/notes/tags`            | None   |
| `GET /api/notes/{id}`            | None   |
| `POST /api/notes`                | None   |
| `PATCH /api/notes/{id}`          | None   |
| `DELETE /api/notes/{id}`         | None   |

---

## Behavior Contract: Tag Normalization on Write

When tags are submitted via POST/PATCH, the backend normalizes each tag:
1. Strip whitespace
2. Convert to lowercase
3. Reject empty strings
4. Deduplicate (order preserved, first occurrence wins)
5. Reject tags > 50 characters

This was already true for NoteService. AccomplishmentService must be updated to match.

**Test**: `POST /api/accomplishments {"title": "T", "tags": ["Leadership", "LEADERSHIP", "  leadership  "]}` → stored tags: `["leadership"]`

---

## Behavior Contract: AND Filter

`GET /api/accomplishments?tag=a&tag=b` returns only records where BOTH "a" AND "b" appear in the tags array.

**Test**:
- Record 1: tags = ["leadership", "technical"]
- Record 2: tags = ["leadership"]
- Record 3: tags = ["technical"]

Query `?tag=leadership&tag=technical` → returns Record 1 only.  
Query `?tag=leadership` → returns Records 1 and 2.  
Query `?tag=technical` → returns Records 1 and 3.
