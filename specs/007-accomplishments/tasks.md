# Tasks: Accomplishments Management (007)

**Input**: Design documents from `specs/007-accomplishments/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Tests**: TDD is **mandatory** per project Constitution (Principle III). Test tasks appear before their implementation counterparts within each phase. Tests MUST fail before implementation begins. MCP tool contract tests are written **before** each tool is implemented, not after.

**Organization**: Tasks grouped by user story for independent implementation, testing, and delivery.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (touches different files, no dependency on incomplete tasks)
- **[Story]**: User story this task belongs to (US1–US5)
- All file paths are relative to the repository root

---

## Phase 1: Setup (Test File Scaffolding)

**Purpose**: Create empty test modules so TDD can start immediately. No implementation yet.

- [X] T001 Create `backend/tests/unit/test_accomplishment_service.py` with an empty test module (docstring + placeholder `pass`) — file must exist so pytest collects it
- [X] T002 [P] Create `backend/tests/contract/test_accomplishment_api.py` with an empty test module (docstring + placeholder `pass`) — file must exist so pytest collects it

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema migration and shared type definitions. MUST complete before any user story work begins.

**⚠️ CRITICAL**: No user story implementation can begin until T003–T005 are done.

- [X] T003 Add `migrate_v2_to_v3()` to `backend/src/persona/migrations.py` — creates the `accomplishment` table with all columns and indexes exactly as defined in `specs/007-accomplishments/data-model.md` § Database Schema; append the function to the `MIGRATIONS` list so `SCHEMA_VERSION` becomes 3
- [X] T004 [P] Add `Accomplishment` and `AccomplishmentSummary` Pydantic models to `backend/src/persona/models.py` — field names, types, and defaults exactly as specified in `specs/007-accomplishments/data-model.md` § Pydantic Models
- [X] T005 [P] Add `Accomplishment` and `AccomplishmentSummary` TypeScript interfaces to `frontend/src/types/resume.ts` — field names and nullability exactly as specified in `specs/007-accomplishments/data-model.md` § TypeScript Types

**Checkpoint**: Run `cd backend && uv run python -c "from persona.migrations import SCHEMA_VERSION; assert SCHEMA_VERSION == 3"` to confirm migration registered.

---

## Phase 3: User Story 1 — Record a New Accomplishment (Priority: P1) 🎯 MVP

**Goal**: A user can create a STAR accomplishment entry (with title required, all other fields optional) and retrieve it by ID via REST, MCP, and UI.

**Independent Test**: `POST /api/accomplishments` with a full STAR payload returns 201 with the stored record; `GET /api/accomplishments/{id}` returns the same record; `create_accomplishment` MCP tool persists and confirms; the UI form submits and shows a success state.

### TDD: Write Failing Tests First ⚠️

> Run `cd backend && uv run pytest tests/unit/test_accomplishment_service.py tests/contract/test_accomplishment_api.py` — ALL tests below MUST FAIL before implementation starts.

- [X] T006 [P] [US1] Add failing unit tests for `create_accomplishment` DB function and `AccomplishmentService.create_accomplishment` to `backend/tests/unit/test_accomplishment_service.py` — test: title required (raises ValueError when blank), all STAR fields stored, tags trimmed and persisted as list, accomplishment_date nullable, `created_at` and `updated_at` are non-empty strings in returned dict
- [X] T007 [P] [US1] Add failing contract tests for `POST /api/accomplishments` and `GET /api/accomplishments/{id}` to `backend/tests/contract/test_accomplishment_api.py` — test: 201 on valid create, 422 on missing title, 200 + full record on GET by ID, 404 on unknown ID; follow the `_make_client` helper pattern from existing contract tests
- [X] T008 [P] [US1] Add failing MCP contract tests for `create_accomplishment` and `get_accomplishment` tools to `backend/tests/contract/test_accomplishment_api.py` — test: `create_accomplishment` with valid args returns a confirmation string (not dict, not exception); `create_accomplishment` with missing title returns a structured error string (no Python traceback); `get_accomplishment` with valid ID returns an accomplishment dict; `get_accomplishment` with unknown ID returns a structured error string; follow FastMCP testing patterns from existing MCP contract tests in the codebase

### Implementation

- [X] T009 [US1] Add `create_accomplishment` and `load_accomplishment` DB functions to `backend/src/persona/database.py` — signatures and behavior exactly as specified in `specs/007-accomplishments/data-model.md` § Database Functions; `create_accomplishment` inserts row and returns the created record via `load_accomplishment`; `load_accomplishment` raises `ValueError(f"Accomplishment {acc_id} not found")` on missing ID
- [X] T010 [US1] Create `backend/src/persona/accomplishment_service.py` with `AccomplishmentService` class containing `create_accomplishment` and `get_accomplishment` methods — constructor takes `DBConnection`; `create_accomplishment` validates title (raises `ValueError` if blank), normalizes tags (trim + deduplicate), validates date format if provided; delegates to DB functions; return `dict[str, Any]`
- [X] T011 [US1] Update `create_router` in `backend/src/persona/api/routes.py` to accept optional `acc_service: AccomplishmentService | None = None` parameter; add `POST /api/accomplishments` (status 201, delegates to `acc_service.create_accomplishment`, catches `ValueError` → 422) and `GET /api/accomplishments/{id}` (delegates to `acc_service.get_accomplishment`, catches `ValueError` → 404) routes inside `if acc_service is not None:` block
- [X] T012 [US1] Create `backend/src/persona/tools/accomplishment_tools.py` with `register_accomplishment_tools(mcp: FastMCP, get_service: Any) -> None` containing `create_accomplishment` and `get_accomplishment` MCP tools — follow the pattern in `backend/src/persona/tools/application_tools.py`; `create_accomplishment` tool accepts `title`, `situation`, `task`, `action`, `result`, `accomplishment_date`, `tags` as params; wrap service calls in `try/except ValueError` and return error description as string; returns confirmation string `f"Created accomplishment '{title}' (id={acc['id']})"`
- [X] T013 [US1] Update `backend/src/persona/server.py` — add `_acc_service: AccomplishmentService | None = None` global and `_get_acc_service()` helper; instantiate `AccomplishmentService(conn)` in both `create_app` and `main` (stdio path) alongside `ApplicationService`; call `register_accomplishment_tools(mcp, _get_acc_service)`; pass `acc_service=_acc_service` to `create_router`
- [X] T014 [P] [US1] Add `createAccomplishment` and `getAccomplishment` async functions to `frontend/src/services/api.ts` — `createAccomplishment(data: Partial<Accomplishment>): Promise<Accomplishment>` uses POST; `getAccomplishment(id: number): Promise<Accomplishment>` uses GET; follow existing function patterns with `fetchWithErrorHandling` + `handleResponse`
- [X] T015 [P] [US1] Write failing component test for AccomplishmentListView create form in `frontend/src/__tests__/components/AccomplishmentListView.test.tsx` — test: "New Accomplishment" button reveals form; form has labeled inputs for Title (required), Situation, Task, Action, Result, Date, Tags; submitting with no title shows an error; valid submit calls `createAccomplishment` mock and shows success
- [X] T016 [US1] Create `frontend/src/components/AccomplishmentListView.tsx` — renders an empty list placeholder and a "New Accomplishment" button that expands a create form with clearly labeled STAR fields (all four always visible with placeholder hint text per FR-013), accomplishment date picker, and tag input; on submit calls `createAccomplishment` and shows the new entry
- [X] T017 [US1] Add an Accomplishments section/tab to `frontend/src/App.tsx` that renders `<AccomplishmentListView />` — follow the same routing/tab pattern used for the Applications section

**Checkpoint**: `make check` passes. `POST /api/accomplishments` → 201. `GET /api/accomplishments/{id}` → 200. MCP `create_accomplishment` tool works. UI form creates and confirms an entry.

---

## Phase 4: User Story 2 — View and Browse Accomplishments (Priority: P2)

**Goal**: A user can retrieve the full list of accomplishments (summaries with title, date, tags — with optional tag filter and text search), fetch a unique tags list for autocomplete, and view the full STAR detail of a single entry.

**Independent Test**: Pre-seed two accomplishments with different tags; `GET /api/accomplishments` returns both in reverse-chronological order as summaries; `GET /api/accomplishments?tag=X` returns only the matching one; `GET /api/accomplishments/tags` returns the merged unique tag list; the UI list shows titles + tags and clicking an entry opens the full STAR detail view.

### TDD: Write Failing Tests First ⚠️

- [X] T018 [P] [US2] Add failing unit tests for `load_accomplishments` (ordering, tag filter, text search) and `load_accomplishment_tags` (sorted unique list) to `backend/tests/unit/test_accomplishment_service.py`
- [X] T019 [P] [US2] Add failing contract tests for `GET /api/accomplishments`, `GET /api/accomplishments?tag=X`, `GET /api/accomplishments?q=Y`, and `GET /api/accomplishments/tags` to `backend/tests/contract/test_accomplishment_api.py` — verify 200, correct shape (AccomplishmentSummary list without STAR body fields, string list), empty list on no match
- [X] T020 [P] [US2] Add failing MCP contract test for `list_accomplishments` tool to `backend/tests/contract/test_accomplishment_api.py` — test: calling with no args returns a list of summary dicts; calling with `tag` filter returns only matching entries; calling with `q` search returns matching entries; empty result returns empty list (not error)

### Implementation

- [X] T021 [US2] Add `load_accomplishments` and `load_accomplishment_tags` DB functions to `backend/src/persona/database.py` — `load_accomplishments` uses the sort query from `specs/007-accomplishments/data-model.md` § Sort query pattern and the tag LIKE filter pattern from § Tag filter pattern; `load_accomplishment_tags` parses JSON arrays in Python (`json.loads`) and returns `sorted(set(tags))`
- [X] T022 [US2] Add `list_accomplishments` and `list_tags` methods to `AccomplishmentService` in `backend/src/persona/accomplishment_service.py` — `list_accomplishments` returns `AccomplishmentSummary`-shaped dicts (id, title, accomplishment_date, tags, timestamps only — no STAR body fields); `list_tags` returns the sorted unique tag list from `load_accomplishment_tags`
- [X] T023 [US2] Add `GET /api/accomplishments/tags` and `GET /api/accomplishments` routes to `backend/src/persona/api/routes.py` — **insert the `/tags` route declaration before the existing `GET /api/accomplishments/{id}` route in the file** (open routes.py, find the `/{id}` route registered in T011, place `/tags` above it to prevent FastAPI matching "tags" as an integer path parameter, per research.md Decision 6); list route accepts optional `tag: str | None` and `q: str | None` query params
- [X] T024 [US2] Add `list_accomplishments` MCP tool to `backend/src/persona/tools/accomplishment_tools.py` — params: `tag: str | None = None`, `q: str | None = None`; wraps service call in `try/except ValueError` and returns error string on failure; returns `list[dict[str, Any]]`; docstring documents both filter params
- [X] T025 [P] [US2] Add `listAccomplishments(tag?: string, q?: string): Promise<AccomplishmentSummary[]>` and `listAccomplishmentTags(): Promise<string[]>` to `frontend/src/services/api.ts`
- [X] T026 [P] [US2] Write failing component test for AccomplishmentDetailView in `frontend/src/__tests__/components/AccomplishmentDetailView.test.tsx` — test: all four STAR sections are rendered with their labels; empty STAR fields show placeholder hint text (not hidden); accomplishment date and tags are displayed; back button fires `onBack` callback
- [X] T027 [US2] Update `frontend/src/components/AccomplishmentListView.tsx` to fetch and display the accomplishment list on mount — renders each entry as a clickable card showing title, accomplishment_date, and tags; includes tag filter input (populated from `listAccomplishmentTags`) and text search input; tag autocomplete suggests from the tags list; empty state shown when list is empty
- [X] T028 [US2] Create `frontend/src/components/AccomplishmentDetailView.tsx` — displays full STAR detail (all four fields always visible with hint text when empty per FR-013), accomplishment date, and tags; accepts `accomplishmentId: number` and `onBack: () => void` props; fetches record via `getAccomplishment`
- [X] T029 [US2] Update `frontend/src/App.tsx` (or `AccomplishmentListView.tsx`) to open `AccomplishmentDetailView` when a list item is clicked — renders detail view in place of list; back button returns to list

**Checkpoint**: `make check` passes. List endpoint returns correct order and filtering as AccomplishmentSummary. Tags endpoint returns sorted unique list. UI list shows entries and opens detail with full STAR content.

---

## Phase 5: User Story 3 — Edit an Accomplishment (Priority: P3)

**Goal**: A user can update any subset of an accomplishment's fields (STAR text, title, date, tags) without overwriting unchanged fields.

**Independent Test**: Create an accomplishment; `PATCH /api/accomplishments/{id}` with only `{"result": "Updated result"}` returns the record with only `result` changed; all other fields retain original values; MCP `update_accomplishment` tool produces the same behavior; UI edit form saves and reflects the change.

### TDD: Write Failing Tests First ⚠️

- [X] T030 [P] [US3] Add failing unit tests for `AccomplishmentService.update_accomplishment` to `backend/tests/unit/test_accomplishment_service.py` — test: partial update leaves untouched fields unchanged, title-to-blank raises ValueError, unknown ID raises ValueError, date format validated, `updated_at` changes after update
- [X] T031 [P] [US3] Add failing contract test for `PATCH /api/accomplishments/{id}` to `backend/tests/contract/test_accomplishment_api.py` — test: 200 with updated record on valid patch, 404 on unknown ID, 422 on blank title
- [X] T032 [P] [US3] Add failing MCP contract test for `update_accomplishment` tool to `backend/tests/contract/test_accomplishment_api.py` — test: valid partial update returns confirmation string; unknown ID returns structured error string (no traceback); blank title returns structured error string

### Implementation

- [X] T033 [US3] Add `update_accomplishment` DB function to `backend/src/persona/database.py` — builds a dynamic `UPDATE` statement from non-None keys in `data` dict; always sets `updated_at = datetime('now')`; raises `ValueError` if no rows affected (not found); returns the updated record via `load_accomplishment`
- [X] T034 [US3] Add `update_accomplishment` method to `AccomplishmentService` in `backend/src/persona/accomplishment_service.py` — validates: title not blank if provided, date format if provided, normalizes tags if provided; raises `ValueError` on not found or invalid input; delegates to DB function
- [X] T035 [US3] Add `PATCH /api/accomplishments/{id}` route to `backend/src/persona/api/routes.py` — delegates to `acc_service.update_accomplishment`; catches `ValueError`: "not found" → 404, others → 422
- [X] T036 [US3] Add `update_accomplishment` MCP tool to `backend/src/persona/tools/accomplishment_tools.py` — all fields except `id` are optional (`str | None = None` or `list[str] | None = None`); builds data dict of non-None values before calling service; wraps in `try/except ValueError` and returns error string on failure; returns confirmation string
- [X] T037 [P] [US3] Add `updateAccomplishment(id: number, data: Partial<Accomplishment>): Promise<Accomplishment>` to `frontend/src/services/api.ts` using PATCH
- [X] T038 [US3] Add inline edit form to `frontend/src/components/AccomplishmentDetailView.tsx` — "Edit" button switches to edit mode; form pre-populates all STAR fields, date, and tags from current record; "Save" calls `updateAccomplishment` and refreshes display; "Cancel" reverts to view mode without saving

**Checkpoint**: `make check` passes. `PATCH` updates only provided fields. UI edit form saves correctly.

---

## Phase 6: User Story 4 — Delete an Accomplishment (Priority: P4)

**Goal**: A user can permanently remove an accomplishment by ID.

**Independent Test**: Create an accomplishment; `DELETE /api/accomplishments/{id}` returns a success message; subsequent `GET /api/accomplishments/{id}` returns 404; second `DELETE` also returns 404; MCP `delete_accomplishment` tool works; UI delete button removes the entry and returns to the list.

### TDD: Write Failing Tests First ⚠️

- [X] T039 [P] [US4] Add failing unit tests for `AccomplishmentService.delete_accomplishment` to `backend/tests/unit/test_accomplishment_service.py` — test: successful delete returns deleted record dict, unknown ID raises ValueError, deleted record no longer retrievable
- [X] T040 [P] [US4] Add failing contract test for `DELETE /api/accomplishments/{id}` to `backend/tests/contract/test_accomplishment_api.py` — test: 200 + message on success, 404 on unknown ID, 404 on second delete
- [X] T041 [P] [US4] Add failing MCP contract test for `delete_accomplishment` tool to `backend/tests/contract/test_accomplishment_api.py` — test: valid delete returns confirmation string containing the deleted entry's title; unknown ID returns structured error string (no traceback)

### Implementation

- [X] T042 [US4] Add `delete_accomplishment` DB function to `backend/src/persona/database.py` — calls `load_accomplishment` first (raises ValueError if not found), then executes `DELETE`, commits, returns the pre-deletion record dict
- [X] T043 [US4] Add `delete_accomplishment` method to `AccomplishmentService` in `backend/src/persona/accomplishment_service.py` — delegates to DB function; raises `ValueError` on not found
- [X] T044 [US4] Add `DELETE /api/accomplishments/{id}` route to `backend/src/persona/api/routes.py` — delegates to `acc_service.delete_accomplishment`; on success returns `{"message": f"Deleted accomplishment '{acc['title']}'"}`; catches `ValueError` → 404
- [X] T045 [US4] Add `delete_accomplishment` MCP tool to `backend/src/persona/tools/accomplishment_tools.py` — accepts `id: int`; wraps service call in `try/except ValueError` and returns structured error string on failure; returns confirmation string with title of deleted entry
- [X] T046 [P] [US4] Add `deleteAccomplishment(id: number): Promise<ApiSuccessResponse>` to `frontend/src/services/api.ts` using DELETE
- [X] T047 [US4] Add delete button with confirmation to `frontend/src/components/AccomplishmentDetailView.tsx` — "Delete" button shows inline confirmation ("Are you sure?"); on confirm calls `deleteAccomplishment` and calls `onBack()` to return to list; on cancel dismisses confirmation

**Checkpoint**: `make check` passes. DELETE endpoint removes the record. UI delete button works with confirmation.

---

## Phase 7: User Story 5 — MCP Integration Verification (Priority: P5)

**Goal**: All five MCP tools conform to the MCP protocol contract across multi-operation sequences. Per-story MCP contract tests (T008, T020, T032, T041) verified each tool individually; this phase verifies cross-tool behavior and integration paths.

**Independent Test**: A full sequence (create → list → update → delete via MCP) completes without errors; all five tools return structured responses (data or error string) and never expose Python tracebacks.

### TDD: Write Failing Tests First ⚠️

- [X] T048 [US5] Add MCP cross-tool integration tests to `backend/tests/contract/test_accomplishment_api.py` — test multi-operation sequences: create → list (verify entry appears) → update → list (verify update reflected) → delete → list (verify entry gone); test that all five tool error responses contain no Python traceback text; verify all five tools have correct param names matching their docstrings

### Implementation

- [X] T049 [US5] Add accomplishment cross-interface integration tests to `backend/tests/integration/test_cross_interface.py` — test that an accomplishment created via the service layer is visible via the REST API (same DB connection); test durability by closing and reopening the DB connection to the same file and verifying the accomplishment is still retrievable (covers SC-006); follow patterns from existing cross-interface tests

**Checkpoint**: `make check` passes. All five MCP tools return structured responses for both success and error paths across multi-step sequences.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final validation, and cleanup.

- [X] T050 Update `README.md` to document the accomplishments feature — add to the "Features" or "Capabilities" section: what accomplishments are, the STAR format, how to access via REST (`/api/accomplishments`), via MCP tools, and via the UI; per Constitution Development Workflow "README updates" rule
- [X] T051 [P] Run `make check` from the repository root and resolve any remaining type errors, lint warnings, or test failures across both frontend and backend
- [X] T052 [P] Validate all scenarios from `specs/007-accomplishments/quickstart.md` against the running application (`make run-local`) — create an accomplishment; **stop and restart the server; verify the accomplishment is still present (SC-006 durability check)**; then test list, filter by tag, get tags, get single, patch, delete via curl; verify UI flows match acceptance scenarios from spec.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user story phases
- **Phase 3 (US1)**: Depends on Phase 2 only — no dependency on US2–US5
- **Phase 4 (US2)**: Depends on Phase 2; reuses DB + service methods from Phase 3 (US1)
- **Phase 5 (US3)**: Depends on Phase 2; shares DB + service file with US1/US2
- **Phase 6 (US4)**: Depends on Phase 2; shares DB + service file with US1/US2/US3
- **Phase 7 (US5)**: Depends on Phases 3–6 all being complete
- **Phase 8 (Polish)**: Depends on Phase 7

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — independently deliverable as create+retrieve MVP
- **US2 (P2)**: Starts after Phase 2 — can run in parallel with US1 (different methods in same files, no task-level conflict); integrates naturally after US1
- **US3 (P3)**: Starts after Phase 2 — can run in parallel with US1+US2; adds to existing service
- **US4 (P4)**: Starts after Phase 2 — can run in parallel with US1+US2+US3; adds to existing service
- **US5 (P5)**: Starts after US1–US4 all complete

### Within Each Story

1. Write failing tests FIRST (TDD red) — all [P] test tasks can start together; now includes REST, unit, AND MCP contract tests
2. Implement DB function(s)
3. Implement service method(s) (depends on DB)
4. Implement route + MCP tool (depends on service; [P] with each other)
5. Implement frontend API function (depends on route shape only; can start after contract tests)
6. Implement frontend component (depends on frontend API function)

### Parallel Opportunities

- T001 + T002: Create both test files simultaneously
- T004 + T005: Add Pydantic models and TypeScript types simultaneously
- Within each story: all three TDD tasks [P] can run in parallel (unit tests + REST contract tests + MCP contract tests); then DB → service → route+MCP tool+frontend in sequence
- US1, US2, US3, US4 can proceed in parallel across the service file (different methods, no conflicts)

---

## Parallel Example: User Story 1

```bash
# Step 1 — Write all three flavours of failing tests in parallel (MUST FAIL before Step 2):
Task T006: "Write failing unit tests for create in backend/tests/unit/test_accomplishment_service.py"
Task T007: "Write failing REST contract tests for POST in backend/tests/contract/test_accomplishment_api.py"
Task T008: "Write failing MCP contract tests for create/get tools in backend/tests/contract/test_accomplishment_api.py"
# Verify: cd backend && uv run pytest tests/unit/test_accomplishment_service.py tests/contract/test_accomplishment_api.py → should FAIL

# Step 2 — Implement backend in sequence:
Task T009: DB functions → Task T010: service → Task T011+T012: route+MCP tool (parallel) → Task T013: wire server

# Step 3 — Frontend in parallel:
Task T014: API functions
Task T015: Failing component test
# Then: Task T016: component → Task T017: App integration
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T005)
3. Complete Phase 3: User Story 1 (T006–T017)
4. **STOP and VALIDATE**: `make check` passes; `POST /api/accomplishments` creates an entry; UI form works
5. Demo and iterate before proceeding to US2+

### Incremental Delivery

1. Setup + Foundational → DB schema and shared types ready
2. US1 → Create & retrieve single accomplishment (**MVP**)
3. US2 → List, browse, detail view + tag autocomplete
4. US3 → Edit (iterative refinement of entries)
5. US4 → Delete (data hygiene)
6. US5 → Full MCP integration verified
7. Polish → README updated, all checks green

Each story adds value without breaking the previous ones.

---

## Notes

- Constitution III mandates TDD: tests MUST fail before implementation starts
- Every MCP tool requires at least one contract test BEFORE it is implemented (Constitution III) — T008, T020, T032, T041 satisfy this per story
- `GET /api/accomplishments/tags` MUST be inserted before `GET /api/accomplishments/{id}` in routes.py (T023 — insert, not append)
- List endpoint returns `AccomplishmentSummary` (no STAR body); full STAR detail requires `GET /api/accomplishments/{id}`
- Tags stored as JSON TEXT array — use `json.loads`/`json.dumps` in database.py; service layer normalizes (trim + deduplicate) before storage
- `updated_at` must be set to `datetime('now')` in every `update_accomplishment` DB call
- All STAR fields default to `""` (empty string) — never NULL in DB; displayed with placeholder hint text in UI
- `accomplishment_date` is nullable TEXT in DB (`None`/`null` allowed); when absent, sort falls back to `created_at`
- Commit after each phase checkpoint; conventional commit format per Constitution
