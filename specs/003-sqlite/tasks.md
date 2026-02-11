# Tasks: SQLite Storage

**Input**: Design documents from `/specs/003-sqlite/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included per Constitution Principle III (Test-Driven Development). Tests are written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration changes and dependency cleanup before implementation begins

- [x] T001 Add `DB_FILENAME = "persona.db"` constant to `src/persona/config.py`
- [x] T002 [P] Remove `python-frontmatter` dependency from `pyproject.toml`

---

## Phase 2: Foundational (Migration Framework)

**Purpose**: Schema migration framework that MUST be complete before any user story work

**CRITICAL**: US2 (auto-init) and US4 (schema upgrades) both depend on this framework

- [x] T003 Write unit tests for migration framework (apply_migrations, v0-to-v1, version mismatch, rollback on failure, no-op when current) in `tests/unit/test_migrations.py`
- [x] T004 Implement migration framework (SchemaVersionError, MigrationError, MIGRATIONS list, apply_migrations(), migrate_v0_to_v1()) in `src/persona/migrations.py`
- [x] T005 Update shared test fixtures — replace markdown fixtures with SQLite `db_conn` and `db_conn_at_version` fixtures in `tests/conftest.py`

**Checkpoint**: Migration framework passes all unit tests. `PRAGMA user_version` tracking works. Error types are defined.

---

## Phase 3: User Story 2 — Database Initializes Automatically (Priority: P1)

**Goal**: Database and schema are created automatically on first use with zero user setup

**Independent Test**: Start the system with no pre-existing data directory → database is created, all tools function

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T006 [US2] Write tests for init_database (creates DB file, sets WAL mode, sets foreign_keys ON, sets busy_timeout, runs migrations, returns connection) in `tests/unit/test_database.py`

### Implementation for User Story 2

- [x] T007 [US2] Implement `init_database(data_dir: Path) -> sqlite3.Connection` with connection pragmas (WAL, foreign_keys, busy_timeout) and migration call in `src/persona/database.py`
- [x] T008 [US2] Wire `init_database()` into server startup — replace `resume_store` initialization with database init in `src/persona/server.py`
- [x] T009 [US2] Update integration test to verify auto-creation of data directory and database file on fresh start in `tests/integration/test_server.py`

**Checkpoint**: Server starts from scratch, creates `~/.persona/persona.db` automatically, schema is at version 1

---

## Phase 4: User Story 1 — Store and Retrieve Resume Data (Priority: P1) MVP

**Goal**: All resume data (contact, summary, experience, education, skills) can be written and read back with 100% fidelity

**Independent Test**: Write resume data via MCP tools, read it back, verify every field matches exactly (SC-001)

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [US1] Write tests for read operations (load_resume returns valid Resume on empty DB, load_section for each section type, round-trip fidelity) in `tests/unit/test_database.py`
- [x] T011 [US1] Write tests for singleton write operations (save_contact partial merge, save_summary full replace, validation errors) in `tests/unit/test_database.py`

### Implementation for User Story 1

- [x] T012 [US1] Implement `load_resume()` and `load_section()` in `src/persona/database.py` — read from all 5 tables, assemble Resume model, handle empty DB gracefully
- [x] T013 [US1] Implement `save_contact()` (INSERT OR REPLACE with partial merge) and `save_summary()` (full replace) in `src/persona/database.py`
- [x] T014 [US1] Update read tool handlers (`get_resume`, `get_resume_section`) to accept `conn` and call database module in `src/persona/tools/read.py`
- [x] T015 [US1] Update write tool handlers (`update_section` for contact/summary) to accept `conn` and call database module in `src/persona/tools/write.py`
- [x] T016 [P] [US1] Update contract tests for read tools with SQLite fixtures in `tests/contract/test_read_tools.py`
- [x] T017 [P] [US1] Update contract tests for `update_section` with SQLite fixtures in `tests/contract/test_write_tools.py`

**Checkpoint**: Contact and summary can be saved and retrieved. `get_resume` returns complete data. Round-trip fidelity verified.

---

## Phase 5: User Story 3 — Manage Resume Entries (Priority: P1)

**Goal**: Users can add, update, and remove individual entries (experience, education, skills) with ordering preserved and duplicates rejected

**Independent Test**: Add entries, modify them, remove them, verify the resume reflects each change correctly

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T018 [US3] Write tests for experience entry management (add prepends at position 0, update by index preserves ordering, remove compacts positions, index out-of-range error) in `tests/unit/test_database.py`
- [x] T019 [US3] Write tests for education entry management (add prepends, update by index, remove compacts, index out-of-range) in `tests/unit/test_database.py`
- [x] T020 [US3] Write tests for skill entry management (add with default category, duplicate name rejection case-insensitive, update by index, remove by index) in `tests/unit/test_database.py`

### Implementation for User Story 3

- [x] T021 [US3] Implement `add_experience()`, `update_experience()`, `remove_experience()` with position management in `src/persona/database.py`
- [x] T022 [US3] Implement `add_education()`, `update_education()`, `remove_education()` with position management in `src/persona/database.py`
- [x] T023 [US3] Implement `add_skill()`, `update_skill()`, `remove_skill()` with case-insensitive duplicate detection in `src/persona/database.py`
- [x] T024 [US3] Update write tool handlers (`add_entry`, `update_entry`, `remove_entry`) to call database module in `src/persona/tools/write.py`
- [x] T025 [US3] Update contract tests for entry operations (`add_entry`, `update_entry`, `remove_entry`) in `tests/contract/test_write_tools.py`

**Checkpoint**: Full CRUD on all entry types works. Ordering preserved. Duplicate skills rejected. All contract tests pass.

---

## Phase 6: User Story 4 — Schema Changes Are Applied Automatically (Priority: P2)

**Goal**: Database schema upgrades are applied transparently on startup, preserving all existing data

**Independent Test**: Create a database at schema version 1, add a test-only v1-to-v2 migration, start system, verify data preserved and schema updated

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T026 [US4] Write tests for multi-step migration (mock v1-to-v2 migration, verify data preserved across upgrade, verify version incremented correctly) in `tests/unit/test_migrations.py`
- [x] T027 [P] [US4] Write integration test for transparent schema upgrade on server startup in `tests/integration/test_server.py`

### Implementation for User Story 4

- [x] T028 [US4] Verify and harden migration rollback — ensure failed migration leaves DB at pre-migration version with clear `MigrationError` in `src/persona/migrations.py`
- [x] T029 [US4] Verify server refuses to start when DB version > code version with clear `SchemaVersionError` message in `src/persona/server.py`

**Checkpoint**: Schema upgrades are automatic and data-preserving. Version mismatch is detected. Failed migrations roll back cleanly.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, removal of old code, and full validation

- [x] T030 Delete `src/persona/resume_store.py` and `tests/unit/test_resume_store.py`
- [x] T031 Remove all `resume_store` imports and references across the codebase
- [x] T032 Update integration tests for full end-to-end SQLite flow in `tests/integration/test_server.py`
- [x] T033 Run `make check` (lint + typecheck + test) and fix any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US2 (Phase 3)**: Depends on Foundational — first story to implement (enables database creation)
- **US1 (Phase 4)**: Depends on US2 (needs working database initialization)
- **US3 (Phase 5)**: Depends on US1 (needs load/save operations to verify entry changes)
- **US4 (Phase 6)**: Depends on Foundational — can run in parallel with US1/US3 if needed
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US2 (P1)**: Can start after Foundational — no dependencies on other stories
- **US1 (P1)**: Depends on US2 (needs `init_database()` for test fixtures and runtime)
- **US3 (P1)**: Depends on US1 (needs `load_resume`/`load_section` to verify mutations)
- **US4 (P2)**: Can start after Foundational — independent of US1/US3

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Database module functions before tool handler updates
- Tool handler updates before contract test updates
- All tests passing before moving to next phase

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T016 and T017 can run in parallel (different test files)
- US4 can run in parallel with US1/US3 (different files, independent concerns)
- T026 and T027 can run in parallel (different test files)

---

## Parallel Example: User Story 3

```bash
# Write all entry management tests in parallel (same file, sequential in practice):
Task T018: "Write tests for experience entry management in tests/unit/test_database.py"
Task T019: "Write tests for education entry management in tests/unit/test_database.py"
Task T020: "Write tests for skill entry management in tests/unit/test_database.py"

# Note: T018-T020 are in the same file so should be done sequentially.
# T021-T023 implement in the same file (database.py) — also sequential.
```

---

## Implementation Strategy

### MVP First (US2 + US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (migration framework)
3. Complete Phase 3: US2 (database auto-initialization)
4. Complete Phase 4: US1 (store and retrieve all resume data)
5. **STOP and VALIDATE**: `make check` passes, resume data round-trips correctly

### Incremental Delivery

1. Setup + Foundational → Migration framework ready
2. Add US2 → Database creates itself → Validate
3. Add US1 → All data readable/writable → Validate (MVP!)
4. Add US3 → Full CRUD on entries → Validate
5. Add US4 → Schema upgrade path proven → Validate
6. Polish → Old code removed, full test suite green → `make check`

### Single-Developer Strategy (Recommended)

Execute phases sequentially in order (1 → 2 → 3 → 4 → 5 → 6 → 7). This is optimal because:
- Each phase builds directly on the previous
- TDD cycle (test → implement → verify) is natural within each phase
- `make check` can be run at each checkpoint to catch regressions early
