# Tasks: Improved Tags Handling

**Input**: Design documents from `/specs/015-tags-handling/`  
**Branch**: `feat-015-tags-handling`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**TDD required** (Constitution III): Write failing tests first, implement until passing, then refactor.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks in the same phase
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (No new setup needed)

No new files, packages, or migrations required. Backend and frontend environments already configured. No Phase 1 tasks.

---

## Phase 2: Foundational — Backend Tag Normalization Fix

**Purpose**: Fix the `AccomplishmentService._normalize_tags` inconsistency (no lowercase) before any other work. This affects existing tests and all new work. Must complete before US1 backend tasks.

**⚠️ CRITICAL**: AccomplishmentService currently does NOT lowercase tags. NoteService does. Research identified this gap. All new contract tests assume tags are lowercase. Fix this first.

- [x] T001 Write failing unit test asserting `AccomplishmentService._normalize_tags` lowercases tags in `backend/tests/unit/test_accomplishment_service.py` (update `test_tags_trimmed_and_persisted` to assert `{"leadership", "technical"}` not `{"Leadership", "Technical"}`)
- [x] T002 Update `_normalize_tags` in `backend/src/persona/accomplishment_service.py` to add `.lower()` (matching NoteService pattern: `normalized = tag.strip().lower()`)
- [x] T003 Run `cd backend && make check` to confirm T001 passes and no regressions

**Checkpoint**: Both services normalize tags identically (lowercase + trim + dedup). `make check` green.

---

## Phase 3: User Story 1 — TagInput Component + Form Tags (Priority: P1) 🎯 MVP

**Goal**: Replace comma-separated tags plain input with chip-based `TagInput` component in all create/edit forms (AccomplishmentListView, NoteListView, AccomplishmentDetailView, NoteDetailView).

**Independent Test**: Open the app. In AccomplishmentListView, click "New Accomplishment", type "leadership" in tags, press Enter → chip appears. Type "team lead", press Enter → multi-word chip appears. Click "×" → chip removed. Submit → saved tags are lowercase chips only.

### Tests for User Story 1

> **Write these FIRST, run to confirm they FAIL, then implement**

- [x] T004 Write Vitest tests for `TagInput` component in `frontend/src/__tests__/components/TagInput.test.tsx` covering:
  - Renders chips for initial `value` array
  - Typing + Enter commits chip and clears input
  - Typing + comma commits chip and clears input
  - Chip "×" click removes that chip
  - Duplicate chip not added (case-insensitive)
  - Empty/whitespace input commit is no-op
  - Autocomplete dropdown appears on typing (matching `availableTags`)
  - "Create new tag: X" option visible when `allowCreate={true}` and input non-empty
  - Clicking dropdown item commits as chip
  - Escape closes dropdown
  - Blur commits non-empty typed text as chip
  - Tags normalized to lowercase on commit

### Implementation for User Story 1

- [x] T005 Create `frontend/src/components/TagInput.tsx` — chip list + text input + autocomplete dropdown component with props: `value: string[]`, `onChange: (tags: string[]) => void`, `availableTags: string[]`, `allowCreate?: boolean`, `placeholder?: string`, `id?: string`
- [x] T006 Create `frontend/src/components/TagInput.module.css` — styles using existing design tokens (`var(--accent-green)`, `var(--accent-green-bg)`, `var(--bg-input)`, `var(--border-primary)`, `var(--radius)`, `var(--font-mono)`). Chip style matches existing `.tagBadge`. Dropdown: absolutely positioned, `var(--bg-hover)` background, `1px solid var(--border-primary)` border.
- [x] T007 [P] Update `frontend/src/components/AccomplishmentListView.tsx` — replace plain tags `<input>` + `<datalist>` in create form with `<TagInput value={form.tags} onChange={...} availableTags={allTags} allowCreate={true} placeholder="Add tag..." />`. Change `FormState.tags` from `string` to `string[]`. Remove comma-split parsing in `handleSave`.
- [x] T008 [P] Update `frontend/src/components/NoteListView.tsx` — same changes as T007 for note create form tags field.
- [x] T009 [P] Update `frontend/src/components/AccomplishmentDetailView.tsx` — replace plain tags `<input>` in edit form with `<TagInput value={editForm.tags ?? []} onChange={(tags) => handleEditFieldChange('tags', tags)} availableTags={allTags} allowCreate={true} />`. Add `allTags` state + `listAccomplishmentTags()` fetch on mount.
- [x] T010 [P] Update `frontend/src/components/NoteDetailView.tsx` — same changes as T009 for note edit form. Add `allTags` state + `listNoteTags()` fetch on mount.
- [x] T011 [P] Update `frontend/src/__tests__/components/AccomplishmentListView.test.tsx` — update tag-related assertions for chip-based TagInput (no longer a plain text input; tags are `string[]` not `string`)
- [x] T012 [P] Update `frontend/src/__tests__/components/NoteListView.test.tsx` — same updates as T011
- [x] T013 [P] Update `frontend/src/__tests__/components/AccomplishmentDetailView.test.tsx` — update tag edit assertions
- [x] T014 [P] Update `frontend/src/__tests__/components/NoteDetailView.test.tsx` — update tag edit assertions
- [x] T015 Run `cd frontend && make check` to confirm T004 passes and no regressions

**Checkpoint**: TagInput component fully tested. All create/edit forms use chip-based tag input. `make check` green. Story 1 independently testable end-to-end.

---

## Phase 4: User Story 2 — Multi-Tag AND Filter (Priority: P2)

**Goal**: Replace single-select `<select>` tag filter on list views with multi-tag chip UI. Backend list endpoints accept multiple `?tag=` params and apply AND logic server-side.

**Independent Test**: On AccomplishmentListView, add "leadership" and "technical" as filter chips. Only accomplishments tagged with BOTH appear. Remove one chip — list updates. Remove all chips — all items shown.

### Tests for User Story 2

> **Write these FIRST, run to confirm they FAIL, then implement**

- [x] T016 Write failing unit tests for multi-tag AND filter in `backend/tests/unit/test_accomplishment_service.py`:
  - `list_accomplishments(tags=["leadership", "technical"])` returns only items with BOTH tags
  - `list_accomplishments(tags=["leadership"])` still works (backward compat)
  - `list_accomplishments(tags=[])` returns all (treat empty list as no filter)
  - `list_accomplishments(tags=["a", "b"])` where no item has both → empty list
- [x] T017 [P] Write failing unit tests for multi-tag AND filter in `backend/tests/unit/test_note_service.py` (same scenarios as T016 for notes)
- [x] T018 Write failing REST contract tests for multi-tag filter in `backend/tests/contract/test_accomplishment_api.py`:
  - `GET /api/accomplishments?tag=leadership&tag=technical` → AND result
  - `GET /api/accomplishments?tag=leadership` → single-tag result unchanged
  - `GET /api/accomplishments` → all results unchanged
- [x] T019 [P] Write failing REST contract tests for multi-tag filter in `backend/tests/contract/test_note_api.py` (same scenarios as T018 for notes)

### Implementation for User Story 2

- [x] T020 Update `load_accomplishments` in `backend/src/persona/database.py` — change `tag: str | None` to `tags: list[str] | None`; build one `tags ILIKE %s` condition per tag joined with AND (e.g., `params.append(f'%"{tag}"%')` for each)
- [x] T021 [P] Update `load_notes` in `backend/src/persona/database.py` — same change as T020 for notes
- [x] T022 Update `AccomplishmentService.list_accomplishments` in `backend/src/persona/accomplishment_service.py` — change signature `tag: str | None` → `tags: list[str] | None`; pass through to `load_accomplishments`
- [x] T023 [P] Update `NoteService.list_notes` in `backend/src/persona/note_service.py` — same change as T022; remove existing `tag.strip().lower()` pre-processing (now handled per-tag in service or DB layer)
- [x] T024 Update `list_accomplishments` route in `backend/src/persona/api/routes.py` — change `tag: str | None = None` to `tag: list[str] | None = Query(default=None)` (add `from fastapi import Query` if not present); pass as `tags=tag`
- [x] T025 [P] Update `list_notes` route in `backend/src/persona/api/routes.py` — same change as T024 for notes route
- [x] T026 Run `cd backend && make check` to confirm T016–T019 pass and no regressions
- [x] T027 Update `listAccomplishments` in `frontend/src/services/api.ts` — change signature from `tag?: string` to `tags?: string[]`; use `tags.forEach(t => params.append('tag', t))` instead of `params.set('tag', tag)`
- [x] T028 [P] Update `listNotes` in `frontend/src/services/api.ts` — same change as T027 for notes
- [x] T029 Update `frontend/src/components/AccomplishmentListView.tsx` — replace `<select>` filter with `<TagInput value={tagFilter} onChange={setTagFilter} availableTags={allTags} allowCreate={false} placeholder="Filter by tag..." />`; change `tagFilter` state from `string` to `string[]`; pass `tagFilter` (array) to `listAccomplishments`
- [x] T030 [P] Update `frontend/src/components/NoteListView.tsx` — same change as T029 for notes filter
- [x] T031 [P] Update `frontend/src/__tests__/components/AccomplishmentListView.test.tsx` — add/update filter tests for multi-tag chip UI (mock `listAccomplishments` with `tags` array)
- [x] T032 [P] Update `frontend/src/__tests__/components/NoteListView.test.tsx` — same updates as T031
- [x] T033 Run `cd frontend && make check` to confirm no regressions

**Checkpoint**: Multi-tag AND filter works across AccomplishmentListView and NoteListView. Backend and frontend tests green. Full `make check` passes.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T034 Run full `make check` from repo root (lint + typecheck + all tests, both backend and frontend) — confirm clean
- [ ] T035 [P] Manual smoke test per quickstart.md: run `make run-local`, verify TagInput chip UI in create/edit forms, verify multi-tag AND filter on list views, verify multi-word tags work (e.g., "soft skills")
- [ ] T036 [P] Update `README.md` to reflect new tag input behavior (chip-based, autocomplete, multi-tag filter with AND logic)

**Checkpoint**: All phases complete. Feature ready for PR.

---

## Dependencies

```
Phase 2 (T001–T003)
  └── Must complete before US1 backend work

Phase 3 / US1 (T004–T015)
  ├── T004 written first (TDD red)
  ├── T005 → T006 → T007, T008, T009, T010 (parallel)
  ├── T007–T014 parallel after T005 + T006
  └── T015 validates all

Phase 4 / US2 (T016–T033)
  ├── T016–T019 written first (TDD red) — can start in parallel with Phase 3
  ├── T020–T025: backend implementation (T020 before T022, T021 before T023)
  ├── T026: backend validate
  ├── T027–T032: frontend (T027+T028 parallel; T029 after T027; T030 after T028)
  └── T033: frontend validate

Phase 5 (T034–T036)
  └── After all phases complete
```

## Parallel Opportunities

**Within Phase 3 (US1)**:
- T007, T008, T009, T010 — four view updates, all different files, parallelizable after T005+T006
- T011, T012, T013, T014 — four test updates, all different files, parallelizable

**Within Phase 4 (US2)**:
- T016 + T017 — unit tests for acc + notes in parallel
- T018 + T019 — contract tests for acc + notes in parallel
- T020 + T021 — DB function updates in parallel (different functions in same file — serialize)
- T022 + T023 — service updates in parallel (different files)
- T024 + T025 — route updates in parallel (same file — serialize)
- T027 + T028 — api.ts updates in parallel (same file — serialize)
- T029 + T030 — view updates in parallel (different files)
- T031 + T032 — test updates in parallel (different files)

**Cross-phase**: Phase 4 TDD tasks (T016–T019) can be written while Phase 3 implementation is in progress.

## Implementation Strategy

**MVP**: Complete Phase 2 + Phase 3 (US1) only. Delivers chip-based tag input in all forms. Users get autocomplete, chip UI, and "Create new tag" without the filter change.

**Full feature**: Add Phase 4 (US2) for multi-tag AND filter. Phase 3 and Phase 4 share the `TagInput` component — Phase 4 reuses it with `allowCreate={false}`.
