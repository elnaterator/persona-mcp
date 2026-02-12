# Tasks: REST API & Remote MCP Server with Docker Support

**Input**: Design documents from `/specs/004-rest-api/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Included per Constitution Principle III (TDD required).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Rename package, update build config, and establish new project structure

- [x] T001 Rename `src/persona/` to `src/backend/` and update all imports across source and test files
- [x] T002 Update `pyproject.toml`: change package discovery to `src/backend`, update entry point to `backend.server:main`, replace `mcp>=1.0.0` with `fastmcp>=2.3.0`, add `fastapi>=0.100.0` and `uvicorn>=0.20.0`
- [x] T003 Create `src/backend/api/__init__.py` (empty package init for REST API routes sub-package)
- [x] T004 Run `uv sync` and `make check` to verify renamed package builds, imports resolve, and all existing tests pass

**Checkpoint**: Package renamed, dependencies updated, all existing tests pass with new imports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create `DBConnection` protocol in `src/backend/db.py` per R-004 (execute, cursor, commit, rollback, close methods)
- [x] T006 Update `src/backend/database.py` to type `init_database()` return as `DBConnection` and keep SQLite-specific code isolated
- [x] T007 Write failing unit tests for `ResumeService` in `tests/unit/test_resume_service.py` covering get_resume, get_section, update_section, add_entry, update_entry, remove_entry (TDD red)
- [x] T008 Implement `ResumeService` class in `src/backend/resume_service.py` with `DBConnection` constructor injection per R-005 — pass all tests from T007 (TDD green)
- [x] T009 Update `src/backend/config.py` to add `PERSONA_PORT` (default 8000), `PERSONA_CORS_ORIGINS` (default empty), and `LOG_LEVEL` (default INFO) config vars
- [x] T010 Update `tests/conftest.py` with `ResumeService` fixture using test DB connection
- [x] T011 Run `make check` to verify foundational layer is solid

**Checkpoint**: Foundation ready — `DBConnection` protocol, `ResumeService`, and config in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Manage Resume via REST API (Priority: P1) MVP

**Goal**: Expose full CRUD for resume data through a standard REST API at `/api/resume` endpoints per openapi.yaml contract.

**Independent Test**: Send HTTP requests (GET, PUT, POST, DELETE) to resume endpoints and verify correct JSON responses with proper status codes.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US1] Write contract tests for GET `/health`, GET `/api/resume`, GET `/api/resume/{section}` in `tests/contract/test_rest_api.py` (TDD red)
- [x] T013 [P] [US1] Write contract tests for PUT `/api/resume/contact`, PUT `/api/resume/summary` in `tests/contract/test_rest_api.py` (TDD red)
- [x] T014 [P] [US1] Write contract tests for POST `/api/resume/{section}/entries`, PUT `/api/resume/{section}/entries/{index}`, DELETE `/api/resume/{section}/entries/{index}` in `tests/contract/test_rest_api.py` (TDD red)
- [x] T015 [P] [US1] Write contract tests for error cases (invalid section 404, out-of-range index 404, validation error 422, malformed JSON 422) in `tests/contract/test_rest_api.py` (TDD red)

### Implementation for User Story 1

- [x] T016 [US1] Implement REST API route handlers in `src/backend/api/routes.py` — health check, GET resume, GET section, PUT contact, PUT summary, POST entry, PUT entry, DELETE entry — using `ResumeService` (TDD green for T012–T015)
- [x] T017 [US1] Wire up FastAPI app creation in `src/backend/server.py` — create FastAPI instance, include API router, add CORS middleware per R-003, add lifespan handler for DB init and `ResumeService` instantiation
- [x] T018 [US1] Update `src/backend/server.py` `main()` to start uvicorn HTTP server as default mode (keep `--stdio` flag for backward compat per R-008)
- [x] T019 [US1] Run all contract tests from T012–T015 and verify they pass (TDD green)

**Checkpoint**: REST API fully functional — all CRUD endpoints respond correctly, error handling works, health check available.

---

## Phase 4: User Story 2 — Access MCP Server Remotely via HTTP (Priority: P2)

**Goal**: Serve existing MCP tools over streamable-http transport at `/mcp` endpoint using FastMCP, mounted on the same FastAPI application.

**Independent Test**: Connect an MCP client to `http://localhost:8000/mcp` and invoke existing MCP tools (get_resume, update_section, etc.).

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [US2] Write integration test verifying MCP tools are accessible via streamable-http transport in `tests/integration/test_server.py` (TDD red)

### Implementation for User Story 2

- [x] T021 [US2] Update MCP tool handlers in `src/backend/tools/read.py` and `src/backend/tools/write.py` to use `ResumeService` instead of direct DB calls
- [x] T022 [US2] Mount FastMCP app at `/mcp` on the FastAPI instance in `src/backend/server.py` per R-001 (use `mcp.http_app(path="/")` and `combine_lifespans`)
- [x] T023 [US2] Verify `--stdio` flag still works for backward-compatible local MCP transport in `src/backend/server.py`
- [x] T024 [US2] Run integration tests from T020 and verify MCP-over-HTTP works (TDD green)

**Checkpoint**: MCP tools accessible via both streamable-http (`/mcp`) and stdio (`--stdio`). Existing MCP functionality preserved.

---

## Phase 5: User Story 3 — Unified Server with Shared State (Priority: P2)

**Goal**: Verify REST API and MCP server share the same `ResumeService` and database connection so changes through one interface are immediately visible through the other.

**Independent Test**: Write via REST API, read via MCP (and vice versa) — verify immediate consistency.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T025 [P] [US3] Write cross-interface integration test: add entry via REST, read via MCP in `tests/integration/test_cross_interface.py` (TDD red)
- [x] T026 [P] [US3] Write cross-interface integration test: update via MCP, read via REST in `tests/integration/test_cross_interface.py` (TDD red)

### Implementation for User Story 3

- [x] T027 [US3] Ensure single `ResumeService` instance is shared between FastAPI routes and MCP tools in `src/backend/server.py` lifespan — verify shared state (TDD green for T025–T026)
- [x] T028 [US3] Run cross-interface tests and verify both directions of shared state work (TDD green)

**Checkpoint**: Changes via REST are visible via MCP and vice versa. Single source of truth confirmed.

---

## Phase 6: User Story 4 — Run Application in Docker Container (Priority: P3)

**Goal**: Package the application in Docker with Docker Compose for consistent deployment across environments.

**Independent Test**: Build Docker image, run container, verify REST API and MCP endpoints respond, verify data persists across restarts.

### Implementation for User Story 4

- [x] T029 [P] [US4] Create `Dockerfile` at repo root — multi-stage build per R-007 (builder with `uv`, slim runtime with `python:3.11-slim`)
- [x] T030 [P] [US4] Create `.dockerignore` at repo root (exclude `.git`, `__pycache__`, `tests/`, `.specify/`, `*.db`)
- [x] T031 [P] [US4] Create `docker-compose.yml` at repo root — single `persona` service with port mapping, volume mount for `./data:/data`, environment variable passthrough, health check per R-007
- [x] T032 [US4] Update `Makefile` — change `make run` to `docker compose up --build`, add `make run-local` for `uv run persona` per R-007
- [x] T033 [US4] Build and test Docker image: `docker compose up --build`, verify health check, REST API, and MCP endpoint respond
- [x] T034 [US4] Test data persistence: stop container, restart with same volume, verify data preserved

**Checkpoint**: Docker image builds, container runs both interfaces, data persists across restarts.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation

- [x] T035 Update `README.md` with REST API usage, Docker instructions, new environment variables, and MCP remote client config (per constitution README update rule)
- [x] T036 Update `CLAUDE.md` active technologies and project layout sections
- [x] T037 Run `make check` (lint + typecheck + test) — all tests pass, no lint errors
- [x] T038 Run quickstart.md validation — manually verify all commands from `specs/004-rest-api/quickstart.md` work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — REST API
- **User Story 2 (Phase 4)**: Depends on Foundational — MCP-over-HTTP; also depends on US1 for shared server setup (T017)
- **User Story 3 (Phase 5)**: Depends on US1 AND US2 (needs both interfaces running to test cross-interface)
- **User Story 4 (Phase 6)**: Depends on US1 and US2 (needs working app to containerize); can run in parallel with US3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational → US1 (independent)
- **US2 (P2)**: Foundational → US1 (server setup) → US2
- **US3 (P2)**: US1 + US2 → US3 (needs both interfaces)
- **US4 (P3)**: US1 + US2 → US4 (can run parallel with US3)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD red)
- Models/protocols before services
- Services before routes/handlers
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T012, T013, T014, T015 (US1 contract tests) can all run in parallel
- T025, T026 (US3 cross-interface tests) can run in parallel
- T029, T030, T031 (US4 Docker files) can all run in parallel
- US3 and US4 can run in parallel once US1+US2 are done

---

## Parallel Example: User Story 1

```bash
# Launch all contract tests in parallel (TDD red):
Task: "Contract test for GET endpoints in tests/contract/test_rest_api.py"
Task: "Contract test for PUT singleton endpoints in tests/contract/test_rest_api.py"
Task: "Contract test for list entry CRUD in tests/contract/test_rest_api.py"
Task: "Contract test for error cases in tests/contract/test_rest_api.py"
```

## Parallel Example: User Story 4

```bash
# Launch all Docker files in parallel:
Task: "Create Dockerfile at repo root"
Task: "Create .dockerignore at repo root"
Task: "Create docker-compose.yml at repo root"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (package rename + deps)
2. Complete Phase 2: Foundational (DBConnection, ResumeService, config)
3. Complete Phase 3: User Story 1 (REST API)
4. **STOP and VALIDATE**: Test REST API independently with curl commands from quickstart.md
5. Deploy/demo if ready — REST API is the primary new capability

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (REST API) → Test independently → **MVP!**
3. Add US2 (MCP-over-HTTP) → Test independently → Remote MCP working
4. Add US3 (Shared state verification) → Confirm cross-interface consistency
5. Add US4 (Docker) → Containerized deployment ready
6. Polish → README, docs, final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD is mandatory per Constitution Principle III: write failing tests first
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
