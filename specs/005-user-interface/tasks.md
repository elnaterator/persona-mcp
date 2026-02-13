# Tasks: Resume Web User Interface

**Input**: Design documents from `/specs/005-user-interface/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included for frontend (Vitest + React Testing Library) and backend changes (pytest) per constitution TDD requirement.

**Organization**: Tasks grouped by user story. US5 (Unified Serving) and US6 (Build Workflow) are infrastructure concerns mapped to Setup and Foundational phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Project Restructure & Scaffolding)

**Purpose**: Restructure repository into monorepo layout, rename Python package, scaffold frontend project, create Makefiles. Covers US5 (Unified Serving) and US6 (Build Workflow) infrastructure.

- [X] T001 Move `src/backend/` to `backend/src/persona/` — rename Python package from `backend` to `persona`, update all `import backend.*` → `import persona.*` in `backend/src/persona/**/*.py`
- [X] T002 Move `tests/` to `backend/tests/` and update all `import backend.*` → `import persona.*` and `from backend.*` → `from persona.*` in `backend/tests/**/*.py`
- [X] T003 Move `pyproject.toml` and `uv.lock` to `backend/`, update `[tool.hatch.build.targets.wheel] packages` to `["src/persona"]`, update entry point to `persona = "persona.server:main"`, update `[tool.ruff] src` to `["src"]`, update `[tool.pytest.ini_options] testpaths` to `["tests"]`, update `[tool.pyright] venvPath`/`venv` paths
- [X] T004 Run `uv sync` in `backend/` to regenerate `.venv` and verify all backend tests pass with `uv run pytest` from `backend/`
- [X] T005 Scaffold frontend React project with Vite + TypeScript template in `frontend/` — create `package.json`, `tsconfig.json`, `vite.config.ts`, `eslint.config.js`, `index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`
- [X] T006 Configure Vite dev server proxy in `frontend/vite.config.ts` — proxy `/api/*`, `/health`, `/mcp` to `http://localhost:8000`
- [X] T007 [P] Create `frontend/Makefile` with targets: `build` (`npm run build`), `run` (`npm run dev`), `lint` (`npm run lint`), `test` (`npm run test`), `check` (lint + test)
- [X] T008 [P] Create `backend/Makefile` with targets: `build` (`uv sync`), `run` (`uv run persona`), `lint` (`uv run ruff check . && uv run ruff format --check .`), `test` (`uv run pytest`), `typecheck` (`uv run pyright`), `check` (lint + typecheck + test), `format` (`uv run ruff format .`)
- [X] T009 Create root `Makefile` with targets: `build` (runs `$(MAKE) -C frontend build && $(MAKE) -C backend build`), `run` (`docker compose up --build`), `run-local` (builds frontend then runs backend), `lint` (both), `test` (both), `check` (both), `format` (both)
- [X] T010 Update root `Dockerfile` for multi-stage build — Stage 1: `node:18-slim` builds frontend (`npm ci && npm run build`), Stage 2: Python builder installs `uv` and syncs deps from `backend/`, Stage 3: Python slim runtime copies `.venv`, `backend/src/`, and `frontend/dist/` into image, CMD `python -m persona.server`
- [X] T011 Update root `docker-compose.yml` — update build context to `.` (root), update environment variables, verify volume mounts and health check path
- [X] T012 Update `.github/workflows/` CI configuration — adjust paths for `backend/` and `frontend/` directories, run `make check` from root or run backend/frontend checks separately
- [X] T013 Verify full setup by running `make check` from root (both frontend and backend lint + test pass)

**Checkpoint**: Repository restructured, both frontend and backend buildable/testable independently, root Makefile orchestrates both.

---

## Phase 2: Foundational (Backend Static Serving + Frontend Core)

**Purpose**: Backend serves frontend static assets from root `/`. Frontend has TypeScript types, API client, and shared UI components. Covers US5 acceptance scenarios.

- [X] T014 Write backend test for static file serving in `backend/tests/integration/test_static_serving.py` — verify: root `/` serves `index.html` when assets exist, API routes still work, MCP endpoint still work s, server starts without frontend assets directory (TDD: write failing test first)
- [X] T015 Add `PERSONA_FRONTEND_DIR` config option to `backend/src/persona/config.py` — resolve to `frontend/dist` relative to repo root (or absolute path via env var), with fallback if directory doesn't exist
- [X] T016 Add `StaticFiles` mount to `backend/src/persona/server.py` — mount at `/` with `html=True` pointing to `PERSONA_FRONTEND_DIR`, register AFTER API router, MCP mount, and health endpoint; skip mount with warning log if directory doesn't exist
- [X] T017 [P] Create TypeScript type definitions in `frontend/src/types/resume.ts` — define `ContactInfo`, `WorkExperience`, `Education`, `Skill`, `Resume` interfaces matching backend Pydantic models (snake_case field names)
- [X] T018 [P] Create API client module in `frontend/src/services/api.ts` — thin `fetch` wrapper with functions: `getResume()`, `getSection(section)`, `updateContact(data)`, `updateSummary(text)`, `addEntry(section, data)`, `updateEntry(section, index, data)`, `removeEntry(section, index)`; handle JSON parsing, error extraction (`detail` field), and HTTP status codes
- [X] T019 [P] Create `LoadingSpinner` component in `frontend/src/components/LoadingSpinner.tsx` with CSS module `LoadingSpinner.module.css`
- [X] T020 [P] Create `StatusMessage` component in `frontend/src/components/StatusMessage.tsx` with CSS module — accepts `type` (success/error), `message`, and optional `onDismiss`; auto-dismisses success messages after timeout
- [X] T021 [P] Create `ConfirmDialog` component in `frontend/src/components/ConfirmDialog.tsx` with CSS module — accepts `message`, `onConfirm`, `onCancel`; used for delete confirmations
- [X] T022 Write tests for API client in `frontend/src/__tests__/services/api.test.ts` — mock `fetch`, verify correct URLs, methods, headers, error handling for each API function

**Checkpoint**: Backend serves frontend assets from `/`, frontend has types + API client + shared components. US5 acceptance scenarios verifiable.

---

## Phase 3: User Story 1 — View Complete Resume (Priority: P1) 🎯 MVP

**Goal**: User navigates to root URL and sees complete resume displayed in a readable layout with all sections.

**Independent Test**: Load root URL, verify all resume sections render with real data.

### Tests for User Story 1

- [X] T023 [P] [US1] Write component test for `ResumeView` in `frontend/src/__tests__/components/ResumeView.test.tsx` — verify: all five sections render when data present, empty state shows when no data, loading spinner shows during fetch
- [X] T024 [P] [US1] Write component test for `ContactSection` (view mode) in `frontend/src/__tests__/components/ContactSection.test.tsx` — verify: all contact fields render, null fields handled gracefully, links render for LinkedIn/website/GitHub

### Implementation for User Story 1

- [X] T025 [P] [US1] Create `ContactSection` component (view mode only) in `frontend/src/components/ContactSection.tsx` with CSS module — display name, email, phone, location, and profile links; handle null fields
- [X] T026 [P] [US1] Create `SummarySection` component (view mode only) in `frontend/src/components/SummarySection.tsx` with CSS module — display summary text; show empty state placeholder when summary is empty
- [X] T027 [P] [US1] Create `ExperienceSection` component (view mode only) in `frontend/src/components/ExperienceSection.tsx` with CSS module — display list of work entries with title, company, dates, location, highlights; show empty state when no entries
- [X] T028 [P] [US1] Create `EducationSection` component (view mode only) in `frontend/src/components/EducationSection.tsx` with CSS module — display list of education entries with institution, degree, field, dates, honors; show empty state when no entries
- [X] T029 [P] [US1] Create `SkillsSection` component (view mode only) in `frontend/src/components/SkillsSection.tsx` with CSS module — display skills grouped by category; show empty state when no skills
- [X] T030 [US1] Create `ResumeView` component in `frontend/src/components/ResumeView.tsx` with CSS module — fetches full resume via `getResume()` on mount, renders all five section components, shows `LoadingSpinner` during fetch, shows error via `StatusMessage` on failure
- [X] T031 [US1] Update `frontend/src/App.tsx` to render `ResumeView` as the root content
- [X] T032 [US1] Add global styles and responsive layout in `frontend/src/index.css` — set up base typography, mobile-first responsive breakpoints (375px–1920px per SC-005), resume-like page layout, handle long text gracefully (word-wrap, overflow for fields up to 5000 chars)

**Checkpoint**: Resume view fully functional. User can see all sections at root URL. Empty states shown for missing data. MVP complete.

---

## Phase 4: User Story 2 — Edit Contact Information and Summary (Priority: P2)

**Goal**: User can edit contact details and summary text via inline forms with save/cancel/validation.

**Independent Test**: Edit contact fields and summary, save, verify changes persist after reload.

### Tests for User Story 2

- [X] T033 [P] [US2] Write component test for `ContactSection` (edit mode) in `frontend/src/__tests__/components/ContactSection.test.tsx` — verify: edit button toggles form, fields pre-filled, save calls API, cancel reverts, validation errors shown
- [X] T034 [P] [US2] Write component test for `SummarySection` (edit mode) in `frontend/src/__tests__/components/SummarySection.test.tsx` — verify: edit button toggles textarea, save calls API, cancel reverts, empty text shows validation error

### Implementation for User Story 2

- [X] T035 [US2] Create `EditableSection` wrapper component in `frontend/src/components/EditableSection.tsx` with CSS module — manages view/edit/saving state machine, provides edit/save/cancel buttons, shows `StatusMessage` for success/error, prevents duplicate submissions during save
- [X] T036 [US2] Add edit mode to `ContactSection` in `frontend/src/components/ContactSection.tsx` — wrap with `EditableSection`, render form with input fields for all 7 contact fields when editing, call `updateContact()` on save, show field-level validation errors
- [X] T037 [US2] Add edit mode to `SummarySection` in `frontend/src/components/SummarySection.tsx` — wrap with `EditableSection`, render textarea when editing, call `updateSummary()` on save, validate non-empty text
- [X] T038 [US2] Update `ResumeView` in `frontend/src/components/ResumeView.tsx` to refresh section data after successful save (re-fetch resume or update local state)

**Checkpoint**: Contact and summary editable with inline forms. Save/cancel/validation working. Edit pattern established for Phase 5.

---

## Phase 5: User Story 3 — Manage List-Based Resume Entries (Priority: P3)

**Goal**: User can add, edit, and delete entries in experience, education, and skills sections.

**Independent Test**: Add a new experience entry, edit an education entry, remove a skill, verify all persist.

### Tests for User Story 3

- [X] T039 [P] [US3] Write component test for `ExperienceSection` (edit/add/delete) in `frontend/src/__tests__/components/ExperienceSection.test.tsx` — verify: add form appears, edit pre-fills, delete shows confirmation, all operations call correct API
- [X] T040 [P] [US3] Write component test for `EntryForm` in `frontend/src/__tests__/components/EntryForm.test.tsx` — verify: renders fields for given config, validates required fields, submits correct data shape

### Implementation for User Story 3

- [X] T041 [US3] Create `EntryForm` component in `frontend/src/components/EntryForm.tsx` with CSS module — generic form that accepts field configuration (name, label, type, required), renders appropriate inputs, validates required fields, handles highlights as dynamic list of text inputs, sizes textareas to accommodate long text (up to 5000 chars)
- [X] T042 [US3] Add add/edit/delete to `ExperienceSection` in `frontend/src/components/ExperienceSection.tsx` — add button opens `EntryForm` for new entry, edit button on each entry opens pre-filled `EntryForm`, delete button shows `ConfirmDialog`, calls `addEntry`/`updateEntry`/`removeEntry` APIs
- [X] T043 [P] [US3] Add add/edit/delete to `EducationSection` in `frontend/src/components/EducationSection.tsx` — same pattern as experience with education-specific fields (institution, degree, field, dates, honors)
- [X] T044 [P] [US3] Add add/edit/delete to `SkillsSection` in `frontend/src/components/SkillsSection.tsx` — same pattern with skill-specific fields (name, category); simpler form than experience/education
- [X] T045 [US3] Update `ResumeView` in `frontend/src/components/ResumeView.tsx` to refresh list data after add/edit/delete operations

**Checkpoint**: All list sections support full CRUD. Add, edit, delete with confirmation all working.

---

## Phase 6: User Story 4 — Responsive Error Handling (Priority: P4)

**Goal**: Errors are displayed clearly without breaking the interface. Unsaved changes preserved on failure.

**Independent Test**: Simulate server errors, verify error messages appear and form data preserved.

### Tests for User Story 4

- [X] T046 [P] [US4] Write component tests for error scenarios in `frontend/src/__tests__/components/ResumeView.test.tsx` — verify: server unavailable shows error with retry, partial load shows per-section errors, failed saves preserve form data

### Implementation for User Story 4

- [X] T047 [US4] Add retry mechanism to `ResumeView` in `frontend/src/components/ResumeView.tsx` — when initial fetch fails, show error message with "Retry" button that re-fetches
- [X] T048 [US4] Add per-section error isolation to `ResumeView` in `frontend/src/components/ResumeView.tsx` — if a section refresh fails after edit, show error on that section only without affecting other sections
- [X] T049 [US4] Ensure `EditableSection` in `frontend/src/components/EditableSection.tsx` preserves form data on save failure — on API error, stay in edit mode with error message displayed, form inputs retain user's values
- [X] T050 [US4] Add network error handling to API client in `frontend/src/services/api.ts` — catch `TypeError` (network failure), return user-friendly error messages, distinguish between network errors and server errors

**Checkpoint**: Error handling comprehensive. Interface remains usable during failures.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Docker integration, documentation, CI updates, final validation.

- [X] T051 [P] Update `CLAUDE.md` with new project layout — update Project Layout section to show `frontend/` and `backend/` structure, update Quick Reference commands, update Active Technologies
- [X] T052 [P] Update `README.md` to reflect new project structure, frontend capability, updated Makefile targets, Docker usage, and development workflow (per constitution README update requirement)
- [X] T053 Build and test Docker container end-to-end — run `docker compose up --build`, verify root `/` serves frontend, `/api/resume` returns data, `/mcp` endpoint works, `/health` returns OK
- [X] T054 Run full `make check` from root — verify frontend lint + test and backend lint + typecheck + test all pass
- [X] T055 Verify `make run-local` works — build frontend, start backend locally, verify root URL serves SPA and API calls work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (T013 checkpoint)
- **US1 (Phase 3)**: Depends on Phase 2 completion (types, API client, shared components)
- **US2 (Phase 4)**: Depends on US1 (builds on view-mode components from Phase 3)
- **US3 (Phase 5)**: Depends on US2 (uses `EditableSection` pattern from Phase 4)
- **US4 (Phase 6)**: Depends on US2 (enhances error handling in existing edit flows)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → US1 (View) → US2 (Edit Contact/Summary) → US3 (List CRUD)
                                                                                    ↘ US4 (Error Handling)
```

- **US1 → US2**: US2 adds edit mode to components created in US1
- **US2 → US3**: US3 reuses the `EditableSection` and `StatusMessage` patterns from US2
- **US2 → US4**: US4 enhances error handling introduced in US2
- **US3 and US4**: Can run in parallel after US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Shared/generic components before specific components
- Parent components (ResumeView) updated last after children are ready

### Parallel Opportunities

- T007, T008 (frontend/backend Makefiles) — different files
- T017, T018, T019, T020, T021 (types, API client, shared components) — all independent files
- T025–T029 (view-mode section components) — all independent files
- T033, T034 (US2 tests) — different test files
- T039, T040 (US3 tests) — different test files
- T043, T044 (education + skills edit modes) — different files, same pattern
- T051, T052 (docs updates) — different files

---

## Parallel Example: User Story 1

```bash
# Launch all section components in parallel (all independent files):
Task: "Create ContactSection (view mode) in frontend/src/components/ContactSection.tsx"
Task: "Create SummarySection (view mode) in frontend/src/components/SummarySection.tsx"
Task: "Create ExperienceSection (view mode) in frontend/src/components/ExperienceSection.tsx"
Task: "Create EducationSection (view mode) in frontend/src/components/EducationSection.tsx"
Task: "Create SkillsSection (view mode) in frontend/src/components/SkillsSection.tsx"

# Then (depends on above):
Task: "Create ResumeView component assembling all sections"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (restructure, scaffold, Makefiles)
2. Complete Phase 2: Foundational (static serving, types, API client)
3. Complete Phase 3: User Story 1 (view resume)
4. **STOP and VALIDATE**: Load root URL, verify resume displays
5. Deploy/demo read-only resume viewer

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. Add US1 (View) → Read-only resume viewer (MVP!)
3. Add US2 (Edit Contact/Summary) → Basic editing
4. Add US3 (List CRUD) → Full editing capability
5. Add US4 (Error Handling) → Production-quality resilience
6. Polish → Docker, docs, CI

### Parallel Opportunities After US2

Once US2 is complete, US3 and US4 can proceed in parallel:
- Developer A: US3 (list entry CRUD)
- Developer B: US4 (error handling improvements)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution requires TDD — write failing tests before implementation
- Package rename (`backend` → `persona`) in T001–T003 is the highest-risk task; verify with T004 before proceeding
- Frontend components use CSS Modules (`.module.css` files) per research decision R4
- API client uses browser `fetch` with thin wrapper per research decision R3
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
