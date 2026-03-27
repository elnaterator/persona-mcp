# Tasks: Personal Context Notes

**Input**: Design documents from `specs/013-personal-context-section/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/notes.yaml

**Tests**: Included — TDD is mandatory per project Constitution (Principle III). Every test task MUST be written and confirmed failing before the corresponding implementation task begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in every description

## Path Conventions

Web application layout:
- `backend/src/persona/` — Python package
- `backend/tests/` — pytest test suite
- `frontend/src/` — React/TypeScript source
- `frontend/src/__tests__/` — Vitest test suite

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Schema and model foundations that MUST exist before any user story can begin.

- [X] T001 Add `migrate_v5_to_v6()` to `backend/src/persona/migrations.py` — creates `note` table (id, user_id FK→users CASCADE, title NOT NULL, content DEFAULT '', tags DEFAULT '[]', created_at, updated_at) with indexes on `user_id` and `updated_at DESC`; append function to `MIGRATIONS` list
- [X] T002 [P] Add `Note` and `NoteSummary` Pydantic models to `backend/src/persona/models.py` — Note has id, title, content, tags (list[str]), created_at, updated_at; NoteSummary omits content
- [X] T003 [P] Add `Note` and `NoteSummary` TypeScript interfaces to `frontend/src/types/resume.ts` — Note has id, title, content, tags (string[]), created_at, updated_at; NoteSummary omits content

**Checkpoint**: Migration and data models defined — user story implementation can now begin

---

## Phase 2: User Story 1 — View and Create Notes (Priority: P1) 🎯 MVP

**Goal**: Users can create a note (title required, content and tags optional) and view their notes as a list and in detail. Data persists across page refreshes.

**Independent Test**: Navigate to the Notes section, create a note with a title and content, verify it appears in the list, click it to open detail view, refresh page and confirm the note is still visible.

### Tests for User Story 1 ⚠️ Write FIRST — confirm FAILING before implementing

- [X] T004 [P] [US1] Write failing unit tests for `create_note` (title required, content optional, returns full Note), `get_note` (returns full Note, raises ValueError if not found), and `list_notes` (returns NoteSummary list ordered by updated_at DESC) in `backend/tests/unit/test_note_service.py`
- [X] T005 [P] [US1] Write failing REST contract tests for `POST /api/notes` (201 created, 422 missing title), `GET /api/notes` (200 list), and `GET /api/notes/{id}` (200 full note, 404 not found) in `backend/tests/contract/test_note_api.py`
- [X] T006 [P] [US1] Write failing NoteListView component tests (renders empty state, renders list of notes, create-note form submits title+content) in `frontend/src/__tests__/components/NoteListView.test.tsx`
- [X] T007 [P] [US1] Write failing NoteDetailView component tests (renders note title and content, renders tags) in `frontend/src/__tests__/components/NoteDetailView.test.tsx`

### Implementation for User Story 1

- [X] T008 [US1] Add `_row_to_note()`, `_row_to_note_summary()` helpers and `create_note()`, `load_note()`, `load_notes()` (with `tag` and `q` params defaulting to None — basic list query only, search/filter ILIKE logic deferred to T036) DB functions to `backend/src/persona/database.py`
- [X] T009 [US1] Create `NoteService` class in `backend/src/persona/note_service.py` with `__init__(conn)`, `create_note(data, user_id)` (validates title required, enforces length limits, basic tag serialization to JSON), `get_note(note_id, user_id)`, and `list_notes(tag, q, user_id)` methods — full tag normalization (_normalize_tags) deferred to T029 (depends on T008)
- [X] T010 [US1] Wire `NoteService` into `backend/src/persona/server.py` — add `_note_service` module-level var, `_get_note_service()` getter, instantiate `NoteService(conn)` in the startup path, pass to MCP tool registration stub and `create_router` (depends on T009)
- [X] T011 [US1] Add `note_service: NoteService | None = None` param to `create_router()` in `backend/src/persona/api/routes.py`; register `POST /api/notes` (201, 422 on ValueError), `GET /api/notes` (accepts `tag` and `q` query params), `GET /api/notes/{note_id}` (200/404/403) routes — register `/tags` route stub (`return []`) **before** `/{note_id}` to prevent FastAPI integer-parse collision (depends on T009)
- [X] T012 [P] [US1] Add `listNotes(tag?, q?)`, `getNote(id)`, and `createNote(data)` async functions to `frontend/src/services/api.ts`
- [X] T013 [P] [US1] Create `frontend/src/components/NoteListView.tsx` — renders Notes section header, empty state when no notes, list of NoteSummary cards (title, tags, updated_at), and a create-note inline form with title (required) and content (optional) fields; tags field with comma-separated input displayed but autocomplete deferred to US3 (depends on T012)
- [X] T014 [US1] Create `frontend/src/components/NoteDetailView.tsx` — reads `:id` param, fetches full Note, renders title, content, tags, timestamps in read-only view; handles 404 with NotFound redirect and 403 with error message (depends on T012)
- [X] T015 [US1] Add `/notes` and `/notes/:id` routes to `frontend/src/router.tsx` importing NoteListView and NoteDetailView (depends on T013, T014)
- [X] T016 [US1] Add Notes nav link/tab to `frontend/src/App.tsx` alongside existing Jobs and Accomplishments links (depends on T015)

**Checkpoint**: US1 complete — create a note via UI, list view shows it, detail view shows full content, data persists on refresh

---

## Phase 3: User Story 2 — Edit and Update Notes (Priority: P2)

**Goal**: Users can open an existing note, edit its title, content, and tags inline, save changes (only changed fields updated), or cancel to discard edits.

**Independent Test**: Create a note, click edit, modify the content, click save — only content changed, title unchanged. Click edit again, modify, click cancel — original content shown.

### Tests for User Story 2 ⚠️ Write FIRST — confirm FAILING before implementing

- [X] T017 [P] [US2] Write failing unit tests for `update_note` (partial update, title blank rejected, not-found raises ValueError) in `backend/tests/unit/test_note_service.py`
- [X] T018 [P] [US2] Write failing REST contract test for `PATCH /api/notes/{id}` (200 updated, 404 not found, 422 blank title, 403 wrong user) in `backend/tests/contract/test_note_api.py`
- [X] T019 [P] [US2] Write failing NoteDetailView edit-mode component tests (edit button shows form, save persists, cancel restores) in `frontend/src/__tests__/components/NoteDetailView.test.tsx`

### Implementation for User Story 2

- [X] T020 [US2] Add `update_note(conn, note_id, data, user_id)` DB function to `backend/src/persona/database.py` — builds SET clause from provided keys only, always sets `updated_at = CURRENT_TIMESTAMP`, raises ValueError if not found
- [X] T021 [US2] Add `update_note(note_id, data, user_id)` method to `NoteService` in `backend/src/persona/note_service.py` — validates title not blank if provided, enforces length limits, normalizes tags if provided (depends on T020)
- [X] T022 [US2] Add `PATCH /api/notes/{note_id}` route to `backend/src/persona/api/routes.py` — 200 on success, 404/403/422 error mapping (depends on T021)
- [X] T023 [P] [US2] Add `updateNote(id, data)` async function to `frontend/src/services/api.ts`
- [X] T024 [US2] Add inline edit mode to `frontend/src/components/NoteDetailView.tsx` — edit button shows form with current title/content/tags pre-filled, save calls updateNote and returns to view mode, cancel discards (depends on T023)

**Checkpoint**: US1+US2 complete — full create/read/update cycle works in UI, REST API, and tests pass

---

## Phase 4: User Story 3 — Tag Notes (Priority: P2)

**Goal**: Users can add free-form tags to notes during create/edit; tags are normalized (lowercased, trimmed, deduplicated); tag input autocompletes from the unified pool of existing note tags and accomplishment tags.

**Independent Test**: Create a note with tags `["Python", "  async  "]`, verify stored as `["python", "async"]`. Open create form, type "pyt" in tag input — "python" appears as autocomplete suggestion.

### Tests for User Story 3 ⚠️ Write FIRST — confirm FAILING before implementing

- [X] T025 [P] [US3] Write failing unit tests for `_normalize_tags` (lowercasing, trimming, deduplication, empty tag removal, max-length enforcement) and `list_tags` (returns sorted unique tags) in `backend/tests/unit/test_note_service.py`
- [X] T026 [P] [US3] Write failing REST contract test for `GET /api/notes/tags` (200 sorted unique list, empty when no notes) in `backend/tests/contract/test_note_api.py`
- [X] T027 [P] [US3] Write failing component tests for tag autocomplete in create form and edit form in `frontend/src/__tests__/components/NoteListView.test.tsx` and `frontend/src/__tests__/components/NoteDetailView.test.tsx`

### Implementation for User Story 3

- [X] T028 [US3] Add `load_note_tags(conn, user_id)` DB function to `backend/src/persona/database.py` — iterates `tags` JSON column for the user, deduplicates with a Python set, returns sorted list
- [X] T029 [US3] Add `_normalize_tags(tags)` helper (trim, lowercase, deduplicate, enforce 50-char max per tag) and `list_tags(user_id)` method to `NoteService` in `backend/src/persona/note_service.py`; update `create_note` and `update_note` to call `_normalize_tags` (depends on T028)
- [X] T030 [US3] Replace the `/tags` stub with the real `GET /api/notes/tags` route in `backend/src/persona/api/routes.py` — calls `note_service.list_tags(uid)` (depends on T029); confirm route remains registered **before** `/{note_id}`
- [X] T031 [P] [US3] Add `listNoteTags()` async function to `frontend/src/services/api.ts`
- [X] T032 [US3] Update tag input in `frontend/src/components/NoteListView.tsx` (create form) and `frontend/src/components/NoteDetailView.tsx` (edit form) to fetch from both `/api/notes/tags` and `/api/accomplishments/tags`, merge client-side, and populate a `<datalist>` for autocomplete (depends on T031)

**Checkpoint**: US1+US2+US3 complete — tags are normalized on save, autocomplete works from unified pool

---

## Phase 5: User Story 5 — Search and Filter Notes (Priority: P2)

**Goal**: Users can search notes by keyword (case-insensitive, multi-word AND matching against title and content) and filter by tag; both can be combined for intersection results.

**Independent Test**: Create three notes with distinct content and tags. Search for a keyword that matches only one — one result shown. Filter by a tag — only tagged notes shown. Apply both — intersection shown. Clear both — all notes shown.

### Tests for User Story 5 ⚠️ Write FIRST — confirm FAILING before implementing

- [X] T033 [P] [US5] Write failing unit tests for `list_notes` with `q` (single word, multi-word AND, case-insensitive) and `tag` filter params in `backend/tests/unit/test_note_service.py`
- [X] T034 [P] [US5] Write failing REST contract tests for `GET /api/notes?q=keyword`, `GET /api/notes?tag=python`, and `GET /api/notes?q=python&tag=async` (intersection) in `backend/tests/contract/test_note_api.py`
- [X] T035 [P] [US5] Write failing component tests for search input and tag filter UI in `frontend/src/__tests__/components/NoteListView.test.tsx`

### Implementation for User Story 5

- [X] T036 [US5] Update `load_notes()` in `backend/src/persona/database.py` to build dynamic WHERE clauses: for each whitespace-split word in `q`, append `(title ILIKE %word% OR content ILIKE %word%)` (AND across words); for `tag`, append `tags ILIKE '%"tag"%'` (depends on T008 which provided the basic function)
- [X] T037 [US5] Verify `list_notes(tag, q, user_id)` in `NoteService` (`backend/src/persona/note_service.py`) passes both params through to the database layer (normalizes tag to lowercase before querying) and that `GET /api/notes` route in `backend/src/persona/api/routes.py` correctly forwards `tag` and `q` query params (added in T011); add test coverage if any gap (depends on T036)
- [X] T038 [P] [US5] Update `listNotes(tag?, q?)` in `frontend/src/services/api.ts` to serialize `tag` and `q` as query string params
- [X] T039 [US5] Add keyword search input and tag-filter dropdown/chips to `frontend/src/components/NoteListView.tsx` — controlled state, calls `listNotes` with current filters on change, shows empty-state message when no results (depends on T038)

**Checkpoint**: US1+US2+US3+US5 complete — search and filter work across title and content; tags and keywords can be combined

*Note: T040 was removed (merged T037+T038 into T037); numbering continues at T041.*

---

## Phase 6: User Story 4 — Delete Notes (Priority: P3)

**Goal**: Users can delete a note by clicking the delete button on the detail view. The note is immediately removed; a non-existent note returns a not-found error.

**Independent Test**: Create a note, navigate to detail view, click delete — note removed from list. Attempt to fetch deleted note ID — 404 response.

### Tests for User Story 4 ⚠️ Write FIRST — confirm FAILING before implementing

- [X] T041 [P] [US4] Write failing unit tests for `delete_note` (returns deleted row, raises ValueError if not found) in `backend/tests/unit/test_note_service.py`
- [X] T042 [P] [US4] Write failing REST contract tests for `DELETE /api/notes/{id}` (200 with message, 404 not found, 403 wrong user) in `backend/tests/contract/test_note_api.py`
- [X] T043 [P] [US4] Write failing NoteDetailView delete component tests (delete button triggers API call, navigates to list on success) in `frontend/src/__tests__/components/NoteDetailView.test.tsx`

### Implementation for User Story 4

- [X] T044 [US4] Add `delete_note(conn, note_id, user_id)` DB function to `backend/src/persona/database.py` — returns deleted row dict, raises ValueError if not found
- [X] T045 [US4] Add `delete_note(note_id, user_id)` method to `NoteService` in `backend/src/persona/note_service.py` (depends on T044)
- [X] T046 [US4] Add `DELETE /api/notes/{note_id}` route to `backend/src/persona/api/routes.py` — returns `{"message": "Deleted note '{title}'"}`, 404/403 error mapping (depends on T045)
- [X] T047 [P] [US4] Add `deleteNote(id)` async function to `frontend/src/services/api.ts`
- [X] T048 [US4] Add delete button to `frontend/src/components/NoteDetailView.tsx` — calls `deleteNote`, navigates to `/notes` list on success (depends on T047)

**Checkpoint**: Full CRUD cycle complete — create, read, update, delete all work via UI and REST API

---

## Phase 7: User Story 6 — Access Notes via MCP (Priority: P3)

**Goal**: AI assistants can list, get, create, update, and delete notes via MCP tools with the same validation and user-scoping as the REST API.

**Independent Test**: Via MCP Inspector or Claude Desktop, call `create_note(title="test")`, verify persisted via `list_notes()`, call `update_note(id=1, content="updated")`, verify change via `get_note(id=1)`, call `delete_note(id=1)`, verify not in `list_notes()`.

### Tests for User Story 6 ⚠️ Write FIRST — confirm FAILING before implementing

- [X] T049 [US6] Write failing MCP contract tests for all 5 note tools (`list_notes`, `get_note`, `create_note`, `update_note`, `delete_note`) — test input schema, success response, missing-title error, not-found error — in `backend/tests/contract/test_note_api.py` following the `_get_tool_fn(mcp, "tool_name")` pattern

### Implementation for User Story 6

- [X] T050 [US6] Create `backend/src/persona/tools/note_tools.py` with `register_note_tools(mcp, get_service)` function registering 5 `@mcp.tool()` decorated functions: `list_notes(tag?, q?)`, `get_note(id)`, `create_note(title, content?, tags?)`, `update_note(id, title?, content?, tags?)`, `delete_note(id)` — each calls `require_user_id()`, calls NoteService, returns string confirmation for mutations and structured error string on ValueError
- [X] T051 [US6] Import and call `register_note_tools(mcp, _get_note_service)` in `backend/src/persona/server.py` (depends on T050, T010)

**Checkpoint**: All 3 interfaces (UI, REST API, MCP) fully functional for all note operations

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Integration validation, documentation, and final verification.

- [X] T052 Add note cross-interface tests to `backend/tests/integration/test_cross_interface.py` — create note via REST, verify visible via MCP `list_notes`; create via MCP `create_note`, verify visible via `GET /api/notes`
- [X] T053 [P] Update `README.md` at repo root to document the Notes section: describe the feature, list REST endpoints (`/api/notes`, `/api/notes/tags`, `/api/notes/{id}`), and MCP tools (`list_notes`, `get_note`, `create_note`, `update_note`, `delete_note`)
- [X] T054 Run `make check` from repo root and confirm all tests pass (backend unit + contract + integration + frontend)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2+ (User Stories)**: Depend on Phase 1 — BLOCKS all stories
- **US1 (Phase 2)**: Depends on Phase 1 only
- **US2 (Phase 3)**: Depends on US1 (NoteDetailView edit mode builds on read-only view)
- **US3 (Phase 4)**: Depends on Phase 1 (tag storage in model), independent of US2
- **US5 (Phase 5)**: Depends on US1 DB function (extends load_notes), independent of US2/US3
- **US4 (Phase 6)**: Depends on Phase 1 only (delete is standalone); can run after US1
- **US6 (Phase 7)**: Depends on US1–US4 backend service methods (tools wrap all service methods)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Start after Phase 1 — no story dependencies
- **US2 (P2)**: Start after US1 — edit mode builds on NoteDetailView from T014; tests can be written in parallel
- **US3 (P2)**: Start after Phase 1 — independent of US2 (different files)
- **US5 (P2)**: Start after US1 (extends load_notes DB function from T008)
- **US4 (P3)**: Start after Phase 1 — independent of all P2 stories
- **US6 (P3)**: Start after all service methods exist (US1–US4 service tasks complete)

### Within Each User Story

1. Write ALL test tasks → confirm they FAIL
2. Implement DB functions
3. Implement service methods (depends on DB)
4. Implement API routes / MCP tools (depends on service)
5. Implement frontend (can overlap with backend once API contract is clear)
6. Run tests → confirm GREEN
7. Mark story complete before moving to next

### Parallel Opportunities

- T001, T002, T003 in Phase 1 can run in parallel (different files)
- T004, T005, T006, T007 in US1 tests can all run in parallel
- T012, T013 (frontend API + component) can run in parallel once T009 contract is clear
- T017, T018, T019 in US2 tests can run in parallel
- T025, T026, T027 in US3 tests can run in parallel
- T033, T034, T035 in US5 tests can run in parallel
- T041, T042, T043 in US4 tests can run in parallel
- T053 (README) can run in parallel with T052

---

## Parallel Example: User Story 1

```bash
# Step 1 — Write all US1 tests in parallel (all failing):
Task T004: unit tests for create_note/get_note/list_notes
Task T005: REST contract tests for POST/GET /api/notes
Task T006: NoteListView component tests
Task T007: NoteDetailView component tests

# Step 2 — Backend implementation (sequential):
T008 (DB functions) → T009 (NoteService) → T010 (server.py) → T011 (routes.py)

# Step 3 — Frontend implementation (parallel with backend steps 3-4):
Task T012: api.ts functions
Task T013: NoteListView component
# Then T014 (NoteDetailView) → T015 (router) → T016 (App.tsx nav)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (T001–T003) — migration + models
2. Complete Phase 2 US1 (T004–T016) — full create/view cycle
3. **STOP and VALIDATE**: `make check` passes; create note via UI and REST API; verify data persists
4. Demo Notes section with create and view functionality

### Incremental Delivery

1. Phase 1 + US1 → **Notes section live with create/view** (MVP!)
2. + US2 → **Notes are editable**
3. + US3 → **Tags with autocomplete**
4. + US5 → **Search and filter**
5. + US4 → **Full CRUD with delete**
6. + US6 → **MCP-accessible for AI workflows**
7. Polish → Integration tests + README

### Parallel Team Strategy

After Phase 1 completes:
- Developer A: US1 (backbone — others depend on this)
- Once US1 backend is done:
  - Developer A: US2 (edit)
  - Developer B: US3 (tags)
  - Developer C: US4 (delete)
- Developer B: US5 (search) after US1 DB function complete
- All converge on US6 (MCP) once service layer is complete

---

## Notes

- `[P]` tasks operate on different files with no in-flight dependencies — safe to parallelize
- `[Story]` label maps each task to a user story for traceability
- Constitution Principle III is non-negotiable: every test task MUST fail before its paired implementation task begins
- `GET /api/notes/tags` route MUST be registered before `GET /api/notes/{note_id}` in routes.py — T011 registers a stub in the correct position; T030 replaces the stub with the real implementation
- Commit after each user story phase completes; use conventional commit format (`feat:`, `test:`, `refactor:`)
- Run `make check` after each phase to catch regressions before moving forward
