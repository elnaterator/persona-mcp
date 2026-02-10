# Tasks: Persona MCP Server with Resume Tools

**Input**: Design documents from `/specs/001-resume-mcp-server/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Required per constitution Principle III (TDD). Tests MUST be written before implementation. Red-Green-Refactor cycle is mandatory.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, packaging, and tooling

- [x] T001 Create project directory structure: `src/persona/`, `src/persona/tools/`, `tests/`, `tests/contract/`, `tests/unit/`, `tests/integration/`
- [x] T002 Create `pyproject.toml` with project metadata, Python 3.11+ requirement, dependencies (`mcp`, `python-frontmatter`), dev dependencies (`pytest`, `pytest-asyncio`, `ruff`, `pyright`), build system (`hatchling`), and entry point `persona = "persona.server:main"`
- [x] T003 [P] Create `Makefile` with mandatory targets: `run` (`uv run persona`), `test` (`uv run pytest`), `lint` (`uv run ruff check . && uv run ruff format --check .`), `typecheck` (`uv run pyright`), `check` (depends on `lint` + `typecheck` + `test`), plus `format` (`uv run ruff format .`)
- [x] T004 [P] Create `src/persona/__init__.py` with package version
- [x] T005 Run `uv sync` to install dependencies and verify `make lint` passes on empty project

**Checkpoint**: Project skeleton compiles, `make lint` passes, `uv run persona` is a valid command (even if it errors on missing server code)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on — config, models, file I/O, server shell

**CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T006 [P] Write unit tests for config module in `tests/unit/test_config.py`: default path `~/.persona/`, env var override `PERSONA_DATA_DIR`, relative path resolution (assert resolved absolute path is logged), directory creation on startup, error on uncreatable path
- [x] T007 [P] Write unit tests for Pydantic models in `tests/unit/test_models.py`: ContactInfo (all optional), WorkExperience (title+company required), Education (institution+degree required), Skill (name required, category defaults to "Other"), Resume aggregate with empty defaults
- [x] T008 [P] Write unit tests for resume store in `tests/unit/test_resume_store.py`: load valid `resume.md`, load empty file (returns empty resume), load malformed front-matter (logs warning, returns defaults), load missing file (returns empty resume), write round-trip (load→modify→save→reload), directory auto-creation

### Implementation for Foundational

- [x] T009 Implement config module in `src/persona/config.py`: resolve data directory from `PERSONA_DATA_DIR` env var (default `~/.persona/`), resolve relative paths against cwd, ensure `jobs/resume/` directory exists, configure `LOG_LEVEL` env var for logging to stderr. Run `make test` — T006 tests pass.
- [x] T010 Implement Pydantic models in `src/persona/models.py`: `ContactInfo`, `WorkExperience`, `Education`, `Skill`, `Resume` per data-model.md entity definitions and validation rules. Run `make test` — T007 tests pass.
- [x] T011 Implement resume store in `src/persona/resume_store.py`: `load_resume(path) -> Resume` and `save_resume(path, resume)` using `python-frontmatter` for file I/O, with Markdown section parsing/serialization per data-model.md file format. Handle edge cases: empty file, malformed front-matter (log warning, return defaults), missing file (return empty resume). Run `make test` — T008 tests pass.
- [x] T012 Create shared test fixtures in `tests/conftest.py`: `tmp_data_dir` fixture (temp directory with `jobs/resume/` structure), `sample_resume_md` fixture (valid `resume.md` content per data-model.md example), `empty_resume_md` fixture
- [x] T013 Create FastMCP server shell in `src/persona/server.py`: instantiate `FastMCP("persona")`, add `main()` function that calls `mcp.run(transport="stdio")`, configure logging to stderr at startup. Verify `make run` starts the server (exits cleanly with no stdin).

**Checkpoint**: Foundation ready — `make check` passes, server starts, config resolves, models validate, resume store reads/writes files

---

## Phase 3: User Story 1 — Read Resume Data (Priority: P1) MVP

**Goal**: An AI assistant can retrieve resume data (full resume or individual sections) via MCP tools

**Independent Test**: Place a sample `resume.md` in the data directory, start the server, issue `get_resume` and `get_resume_section` tool calls, verify correct structured data is returned

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T014 [P] [US1] Write contract tests for `get_resume` tool in `tests/contract/test_read_tools.py`: returns full resume structure from valid file, returns empty resume when file is absent, returns empty resume when file is empty, handles malformed file gracefully
- [x] T015 [P] [US1] Write contract tests for `get_resume_section` tool in `tests/contract/test_read_tools.py`: returns contact info for section="contact", returns experience list for section="experience", returns summary string for section="summary", returns education list for section="education", returns skills list for section="skills", returns error for invalid section name

### Implementation for User Story 1

- [x] T016 [US1] Implement `get_resume` tool in `src/persona/tools/read.py`: register with FastMCP server, load resume via store, return serialized Resume model. Run `make test` — T014 tests pass.
- [x] T017 [US1] Implement `get_resume_section` tool in `src/persona/tools/read.py`: accept `section` enum parameter, validate section name, return corresponding section data. Run `make test` — T015 tests pass.
- [x] T018 [US1] Register read tools with server in `src/persona/tools/__init__.py` and import in `src/persona/server.py`
- [x] T019 [US1] Write integration test in `tests/integration/test_server.py`: start server, invoke `get_resume` and `get_resume_section` via MCP client, verify responses match sample data, assert response time <2s with a 50-entry fixture (SC-001). Run `make check`.

**Checkpoint**: User Story 1 complete — `get_resume` and `get_resume_section` work end-to-end, `make check` passes

---

## Phase 4: User Story 2 — Update Resume Data (Priority: P2)

**Goal**: An AI assistant can add, update, and remove resume entries via MCP tools, with changes persisted to `resume.md`

**Independent Test**: Issue `add_entry`, `update_entry`, `remove_entry`, and `update_section` tool calls, then read back data to verify changes persisted

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [P] [US2] Write contract tests for `update_section` tool in `tests/contract/test_write_tools.py`: update contact fields (partial update preserves other fields), update summary text, error on invalid section, error on empty contact update, error on empty summary text
- [x] T021 [P] [US2] Write contract tests for `add_entry` tool in `tests/contract/test_write_tools.py`: add experience entry (prepended), add education entry, add skill with category, add skill with default "Other" category, error on missing required fields per section, error on duplicate skill name
- [x] T022 [P] [US2] Write contract tests for `update_entry` tool in `tests/contract/test_write_tools.py`: update experience by index (partial update), update education by index, update skill by index, error on out-of-range index, error on empty data
- [x] T023 [P] [US2] Write contract tests for `remove_entry` tool in `tests/contract/test_write_tools.py`: remove experience by index, remove education by index, remove skill by index, error on out-of-range index, error on invalid section

### Implementation for User Story 2

- [x] T024 [US2] Implement `update_section` tool in `src/persona/tools/write.py`: accept section (contact|summary) and data dict, dispatch to section-specific validation, update resume via store, return confirmation. Run `make test` — T020 tests pass.
- [x] T025 [US2] Implement `add_entry` tool in `src/persona/tools/write.py`: accept section (experience|education|skills) and data dict, validate via section-specific Pydantic model, prepend entry, save via store, return confirmation. Run `make test` — T021 tests pass.
- [x] T026 [US2] Implement `update_entry` tool in `src/persona/tools/write.py`: accept section, index, and data dict, validate index bounds, partial-update entry fields, save via store, return confirmation. Run `make test` — T022 tests pass.
- [x] T027 [US2] Implement `remove_entry` tool in `src/persona/tools/write.py`: accept section and index, validate index bounds, remove entry, save via store, return confirmation. Run `make test` — T023 tests pass.
- [x] T028 [US2] Register write tools with server in `src/persona/tools/__init__.py`
- [x] T029 [US2] Write integration test in `tests/integration/test_server.py`: start server, add an experience entry via `add_entry`, read back via `get_resume_section`, verify the entry exists; update it via `update_entry`, verify change; remove it via `remove_entry`, verify gone. Run `make check`.

**Checkpoint**: User Story 2 complete — all write tools work end-to-end, `make check` passes

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Edge case hardening, logging, documentation, final validation

- [x] T030 [P] Add edge case handling: write permission errors return clear ToolError messages (not stack traces), read operations continue working when writes fail, per spec edge cases
- [x] T031 [P] Add logging throughout: log data directory path at startup, log each tool invocation at INFO level, log parse warnings at WARNING level, all to stderr per FR-008
- [x] T032 Verify `make check` passes (lint clean, typecheck clean, all tests green)
- [x] T033 Run quickstart.md validation: follow quickstart.md steps on a clean environment, verify server starts, tools respond, Claude Desktop config works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion. Can technically run in parallel with US1, but US2 write tools benefit from having read tools available for verification
- **Polish (Phase 5)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Recommended to complete after US1 since integration tests use read tools to verify writes

### Within Each User Story

- Contract tests MUST be written and FAIL before implementation (TDD red)
- Implementation tasks run sequentially within each tool (TDD green)
- Integration test runs last to verify end-to-end behavior
- `make check` must pass at each checkpoint

### Parallel Opportunities

- T003 and T004 can run in parallel (different files)
- T006, T007, T008 can run in parallel (different test files)
- T014 and T015 can run in parallel (same file but independent test classes)
- T020, T021, T022, T023 can run in parallel (same file but independent test classes)
- T030 and T031 can run in parallel (different concerns)

---

## Parallel Example: User Story 1

```bash
# Launch all contract tests for US1 together (TDD red):
Task: "Contract test for get_resume in tests/contract/test_read_tools.py"
Task: "Contract test for get_resume_section in tests/contract/test_read_tools.py"

# Then implement sequentially (TDD green):
Task: "Implement get_resume in src/persona/tools/read.py"
Task: "Implement get_resume_section in src/persona/tools/read.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `make check` passes, `get_resume` and `get_resume_section` return correct data
5. Server is usable as a read-only resume assistant

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP (read-only resume)
3. Add User Story 2 → Test independently → Full read-write resume management
4. Polish → Edge case hardening, logging, documentation validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- TDD is mandatory per constitution Principle III — all tool tests must fail before implementation
- Commit after each task or logical group using conventional commits
- Stop at any checkpoint to validate story independently
