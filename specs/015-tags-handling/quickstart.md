# Quickstart: Improved Tags Handling

**Feature**: 015-tags-handling  
**Date**: 2026-04-23

---

## What Changes

This feature replaces the comma-separated plain text tags input with a chip-based autocomplete `TagInput` component, and upgrades the list-view tag filter from a single-select `<select>` to a multi-select chip UI with AND logic.

---

## Files Touched

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/components/TagInput.tsx` | New shared chip input component |
| `frontend/src/components/TagInput.module.css` | Styles for TagInput |
| `frontend/src/__tests__/components/TagInput.test.tsx` | Vitest tests for TagInput |

### Modified Files — Backend

| File | Change |
|------|--------|
| `backend/src/persona/accomplishment_service.py` | Add lowercase to `_normalize_tags`; change `list_accomplishments` sig to `tags: list[str] \| None` |
| `backend/src/persona/note_service.py` | Change `list_notes` sig to `tags: list[str] \| None` |
| `backend/src/persona/database.py` | Change `load_accomplishments` / `load_notes` to `tags: list[str] \| None`; build AND conditions |
| `backend/src/persona/api/routes.py` | Change `tag: str \| None` to `tag: list[str] \| None = Query(default=None)` for both list endpoints |
| `backend/tests/unit/test_accomplishment_service.py` | Update `test_tags_trimmed_and_persisted` to assert lowercase; add multi-tag filter tests |
| `backend/tests/unit/test_note_service.py` | Add multi-tag filter tests |
| `backend/tests/contract/test_accomplishment_api.py` | Add REST multi-tag filter tests; update existing tag normalization assertions |
| `backend/tests/contract/test_note_api.py` | Same as accomplishment contract tests |

### Modified Files — Frontend

| File | Change |
|------|--------|
| `frontend/src/services/api.ts` | `listAccomplishments(tags?)` and `listNotes(tags?)` accept `string[]`, append multiple `?tag=` params |
| `frontend/src/components/AccomplishmentListView.tsx` | Use `TagInput` for form tags + filter |
| `frontend/src/components/NoteListView.tsx` | Use `TagInput` for form tags + filter |
| `frontend/src/components/AccomplishmentDetailView.tsx` | Use `TagInput` for edit form tags |
| `frontend/src/components/NoteDetailView.tsx` | Use `TagInput` for edit form tags |
| `frontend/src/__tests__/components/AccomplishmentListView.test.tsx` | Update tag-related test assertions |
| `frontend/src/__tests__/components/NoteListView.test.tsx` | Update tag-related test assertions |
| `frontend/src/__tests__/components/AccomplishmentDetailView.test.tsx` | Update tag-related test assertions |
| `frontend/src/__tests__/components/NoteDetailView.test.tsx` | Update tag-related test assertions |

---

## Implementation Order (TDD)

Per Constitution III (TDD), tests are written before implementation.

### Step 1: Backend — tag normalization fix (no API change)
1. Write failing test: `AccomplishmentService` normalizes tags to lowercase
2. Update `_normalize_tags` in `accomplishment_service.py` to lowercase
3. `make check` passes

### Step 2: Backend — multi-tag AND filter
1. Write failing tests: `list_accomplishments(tags=["a","b"])` returns AND intersection
2. Update `load_accomplishments` in `database.py` to accept `tags: list[str] | None`
3. Update `AccomplishmentService.list_accomplishments` signature
4. Repeat for notes
5. Write failing REST contract tests: `GET /api/accomplishments?tag=a&tag=b`
6. Update FastAPI routes
7. `make check` passes

### Step 3: Frontend — TagInput component
1. Write Vitest tests for `TagInput` (commit, remove, autocomplete, dedup, no-create filter mode)
2. Implement `TagInput.tsx` + `TagInput.module.css`
3. `make check` passes

### Step 4: Frontend — wire TagInput into views
1. Update `api.ts` (listAccomplishments/listNotes signatures)
2. Update AccomplishmentListView, NoteListView, AccomplishmentDetailView, NoteDetailView
3. Update existing component tests
4. `make check` passes

---

## Verify Locally

```bash
make run-local
# Open http://localhost:8000
# Navigate to /accomplishments
# Type in tags field → autocomplete dropdown appears
# Press Enter → chip appears
# Add two filter tags → AND filter applied
# Navigate to an accomplishment → edit tags → chip UI works
```

```bash
cd backend && make check   # backend lint + typecheck + tests
cd frontend && make check  # frontend lint + tests
```
