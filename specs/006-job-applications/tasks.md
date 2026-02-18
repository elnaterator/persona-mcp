# Tasks: Job Application Management (rev 3)

**Input**: Design documents from `/specs/006-job-applications/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: TDD is mandated by the project constitution. Tests are written FIRST and must FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Project initialization — no behavioral changes, just structure for new code

- [x] T001 Add new Pydantic models (ResumeVersion, Application, ApplicationContact, Communication) to backend/src/persona/models.py per data-model.md entity definitions
- [x] T002 Create empty backend/src/persona/application_service.py with ApplicationService class skeleton (constructor takes DBConnection)
- [x] T003 [P] Create empty backend/src/persona/tools/resume_tools.py module with docstring
- [x] T004 [P] Create empty backend/src/persona/tools/application_tools.py module with docstring
- [x] T005 [P] Create empty backend/src/persona/tools/__init__.py

**Checkpoint**: Project structure ready. No behavior changes yet. `make check` still passes.

---

## Phase 2: Foundational (Schema Migration + Resume Version Core)

**Purpose**: Migrate existing singleton resume to resume versions. This MUST complete before any user story work — it replaces the entire resume storage layer.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The old singleton resume tables are dropped and replaced by the resume_version table.

### Tests (write FIRST, must FAIL)

- [x] T006 Write migration tests in backend/tests/unit/test_migrations.py: test migrate_v1_to_v2 creates resume_version table, migrates existing resume data into default version (is_default=1, label="Default Resume"), drops old tables (contact, summary, experience, education, skill). Test empty DB migration creates empty default version.
- [x] T007 [P] Write unit tests in backend/tests/unit/test_database.py for resume version DB operations: create_resume_version, load_resume_version, load_resume_versions, update_resume_version_metadata, update_resume_version_data, delete_resume_version, set_default_resume_version, load_default_resume_version. Test JSON blob serialization/deserialization round-trip. Test default invariant enforcement: (a) deleting the default when other versions exist auto-promotes the most recently updated version, (b) deleting the last remaining version is rejected, (c) setting default unsets the previous default in the same transaction.
- [x] T008 [P] Write unit tests in backend/tests/unit/test_resume_service.py for updated ResumeService: get_resume(id), get_resume(None)→default, get_section(id, section), update_section(id, section, data), add_entry(id, section, data), update_entry(id, section, index, data), remove_entry(id, section, index), create_resume(label), list_resumes(), set_default(id), delete_resume(id). Test version isolation (editing one doesn't affect another).

### Implementation

- [x] T009 Implement migrate_v1_to_v2 in backend/src/persona/migrations.py: create resume_version table per data-model.md, read existing data from old tables, serialize to JSON blob, insert as default version, drop old tables. Add to MIGRATIONS list.
- [x] T010 Implement resume version database operations in backend/src/persona/database.py: create_resume_version, load_resume_version(id), load_resume_versions (list with app_count), load_default_resume_version, update_resume_version_metadata(id, label), update_resume_version_data(id, resume_data_json), delete_resume_version(id), set_default_resume_version(id). All operations work with JSON blob column.
- [x] T011 Refactor backend/src/persona/resume_service.py to be version-aware: all get/update/add/remove operations take a version_id parameter. get_resume and get_section accept optional id (None=default). Add create_resume(label), list_resumes(), set_default(id), delete_resume(id). Remove old singleton load_resume/load_section calls.
- [x] T012 Update backend/tests/conftest.py: update shared fixtures to use resume_version table instead of old singleton tables. Ensure test DB uses v2 schema.

**Checkpoint**: Resume data migrated. ResumeService operates on versions. Old singleton tables gone. `make test` passes for backend.

---

## Phase 3: User Story 4 — Manage Resumes (Priority: P4, implemented first as foundation)

**Goal**: Full resume version management via REST API, MCP tools, and UI. Users can list versions, create from default, edit any version's sections, change default, delete versions.

**Why first**: Although spec labels this P4, the resume version system replaces the existing resume API and is a prerequisite for all other stories (applications reference resume versions). The old API must be replaced before building on top of it.

**Independent Test**: List resumes, create a version, edit its sections, change default, associate with an application (once apps exist), delete a version.

### Tests (write FIRST, must FAIL)

- [x] T013 [US4] Write contract tests for resume version REST API in backend/tests/contract/test_rest_api.py: GET /api/resumes (list), POST /api/resumes (create from default), GET /api/resumes/default, GET /api/resumes/{id}, PUT /api/resumes/{id} (update label), DELETE /api/resumes/{id} (including 409 for last version), PUT /api/resumes/{id}/default (set default), GET /api/resumes/{id}/{section}, PUT /api/resumes/{id}/contact, PUT /api/resumes/{id}/summary, POST /api/resumes/{id}/{section}/entries, PUT /api/resumes/{id}/{section}/entries/{index}, DELETE /api/resumes/{id}/{section}/entries/{index}
- [x] T014 [P] [US4] Write contract tests for resume version MCP tools in backend/tests/contract/test_read_tools.py and backend/tests/contract/test_write_tools.py: list_resumes, get_resume (with id and without), get_resume_section, update_resume_section, add_resume_entry, update_resume_entry, remove_resume_entry, create_resume, set_default_resume, delete_resume

### Implementation

- [x] T015 [US4] Replace old resume REST routes in backend/src/persona/api/routes.py: remove all /api/resume/* routes. Add /api/resumes/* routes per contracts/rest-api.md — list, create, get default, get by id, update metadata, delete, set default, get section, update contact, update summary, add/update/remove entries. All routes delegate to ResumeService with version_id.
- [x] T016 [US4] Implement resume version MCP tools in backend/src/persona/tools/resume_tools.py: list_resumes, get_resume, get_resume_section, update_resume_section, add_resume_entry, update_resume_entry, remove_resume_entry, create_resume, set_default_resume, delete_resume. Register on shared FastMCP instance.
- [x] T017 [US4] Update backend/src/persona/server.py: remove old 6 MCP tool definitions. Import and register tools from tools/resume_tools.py. Update create_app to pass services to router.
- [x] T018 [P] [US4] Update frontend/src/types/resume.ts: add ResumeVersion interface (id, label, is_default, resume_data, app_count, created_at, updated_at)
- [x] T019 [US4] Update frontend/src/services/api.ts: replace old resume API calls with version-scoped calls — listResumes, getResume(id), getDefaultResume, createResume(label), deleteResume(id), setDefaultResume(id), updateContact(id, data), updateSummary(id, text), addEntry(id, section, data), updateEntry(id, section, index, data), removeEntry(id, section, index)
- [x] T020 [US4] Create frontend/src/components/ResumeListView.tsx: list all resume versions showing label, default badge, app count, created date. "New Version" button (copies default). "Set as Default" action per version. "Delete" action with confirmation (prevent if only version).
- [x] T021 [US4] Create frontend/src/components/ResumeDetailView.tsx: display a single resume version with label header and all section components. Reuses ContactSection, SummarySection, ExperienceSection, EducationSection, SkillsSection passing versionId prop.
- [x] T022 [US4] Update frontend/src/components/ContactSection.tsx, SummarySection.tsx, ExperienceSection.tsx, EducationSection.tsx, SkillsSection.tsx: add optional versionId prop. When present, use version-scoped API calls (/api/resumes/{id}/...). Update all internal API call sites.
- [x] T023 [P] [US4] Write frontend component tests in frontend/src/__tests__/ for ResumeListView and ResumeDetailView

**Checkpoint**: Resume version management fully works across REST, MCP, and UI. Old /api/resume routes removed. `make check` passes.

---

## Phase 4: User Story 1 — Create and Track Job Applications (Priority: P1)

**Goal**: Users can create, list, view, update status, and delete job applications. Applications can optionally reference a resume version.

**Independent Test**: Create an application, see it in the list, update status, verify persistence, delete with cascade confirmation.

### Tests (write FIRST, must FAIL)

- [x] T024 Write unit tests for application database operations in backend/tests/unit/test_database.py: create_application, load_application, load_applications (with status filter and q search), update_application, delete_application (cascade). Test resume_version_id FK (SET NULL on version delete). Test updated_at ordering.
- [x] T025 [P] Write unit tests for ApplicationService in backend/tests/unit/test_application_service.py: create, get, list (filter/search), update, delete
- [x] T026 [P] Write contract tests for application REST API in backend/tests/contract/test_rest_api.py: GET /api/applications (list, filter, search), POST /api/applications, GET /api/applications/{id}, PUT /api/applications/{id}, DELETE /api/applications/{id}
- [x] T027 [P] Write contract tests for application MCP tools in backend/tests/contract/test_write_tools.py: list_applications, get_application, create_application, update_application, delete_application

### Implementation

- [x] T028 Implement application database operations in backend/src/persona/database.py: create_application, load_application(id), load_applications(status, q), update_application(id, data), delete_application(id). Application table created in v1→v2 migration. Include resume_version_id in create/update.
- [x] T029 Implement ApplicationService in backend/src/persona/application_service.py: create, get, list (with filter/search), update, delete. Delegates to database functions. Validates status values, non-empty company/position.
- [x] T030 Add application REST routes to backend/src/persona/api/routes.py: GET/POST /api/applications, GET/PUT/DELETE /api/applications/{id} per contracts/rest-api.md
- [x] T031 Implement application MCP tools in backend/src/persona/tools/application_tools.py: list_applications, get_application, create_application, update_application, delete_application. Register on shared FastMCP instance.
- [x] T032 Update backend/src/persona/server.py: import and register tools from tools/application_tools.py. Pass ApplicationService to router.
- [x] T033 [P] Add application TypeScript types to frontend/src/types/resume.ts: Application interface (id, company, position, description, status, url, notes, resume_version_id, created_at, updated_at)
- [x] T034 Add application API calls to frontend/src/services/api.ts: listApplications(status?, q?), getApplication(id), createApplication(data), updateApplication(id, data), deleteApplication(id)
- [x] T035 Create frontend/src/components/ApplicationListView.tsx: list applications with status badges, sorted by updated_at desc. Status filter dropdown. Search input for company/position. "New Application" button. Click to open detail.
- [x] T036 Create frontend/src/components/ApplicationDetailView.tsx: show full application details — company, position, description, status selector, URL, notes, associated resume version link. Edit fields inline. Delete button with cascade warning.
- [x] T037 Create frontend/src/components/Navigation.tsx: top-level nav bar with "Resumes" and "Applications" links. State-based view switching.
- [x] T038 Update frontend/src/App.tsx: replace single ResumeView with Navigation + state-based routing between ResumeListView, ResumeDetailView, ApplicationListView, ApplicationDetailView
- [x] T039 [P] Write frontend component tests in frontend/src/__tests__/ for ApplicationListView and ApplicationDetailView

**Checkpoint**: Application CRUD fully works. Users can create, list, filter, update, and delete applications across all interfaces. `make check` passes.

---

## Phase 5: User Story 2 — Manage Contacts for a Job Application (Priority: P2)

**Goal**: Users can add, update, and remove contacts (recruiters, hiring managers) for each application.

**Independent Test**: Add a contact to an application, view contacts list, edit contact details, remove a contact.

### Tests (write FIRST, must FAIL)

- [x] T040 Write unit tests for contact database operations in backend/tests/unit/test_database.py: create_contact, load_contacts(app_id), update_contact, delete_contact (verify communications get contact_id set to null)
- [x] T041 [P] Write contract tests for contact REST API in backend/tests/contract/test_rest_api.py: GET/POST /api/applications/{id}/contacts, PUT/DELETE /api/applications/{id}/contacts/{contact_id}
- [x] T042 [P] Write contract tests for contact MCP tools in backend/tests/contract/test_write_tools.py: add_application_contact, update_application_contact, remove_application_contact

### Implementation

- [x] T043 Implement contact database operations in backend/src/persona/database.py: create_contact(app_id, data), load_contacts(app_id), update_contact(id, data), delete_contact(id)
- [x] T044 Add contact methods to ApplicationService in backend/src/persona/application_service.py: add_contact, list_contacts, update_contact, remove_contact
- [x] T045 Add contact REST routes to backend/src/persona/api/routes.py: GET/POST /api/applications/{id}/contacts, PUT/DELETE /api/applications/{id}/contacts/{contact_id}
- [x] T046 Add contact MCP tools to backend/src/persona/tools/application_tools.py: add_application_contact, update_application_contact, remove_application_contact
- [x] T047 [P] Add contact TypeScript types to frontend/src/types/resume.ts: ApplicationContact interface
- [x] T048 Add contact API calls to frontend/src/services/api.ts: listContacts(appId), addContact(appId, data), updateContact(appId, contactId, data), removeContact(appId, contactId)
- [x] T049 Create frontend/src/components/ContactsPanel.tsx: list contacts for an application, add/edit/remove contacts inline. Show name, role, email. Used within ApplicationDetailView.
- [x] T050 Integrate ContactsPanel into frontend/src/components/ApplicationDetailView.tsx

**Checkpoint**: Contact management works for all applications across all interfaces. `make check` passes.

---

## Phase 6: User Story 3 — Track Communications (Priority: P3)

**Goal**: Users can log, view, edit, and status-track communications for each application.

**Independent Test**: Add a communication, view timeline, edit entry, transition through statuses (draft → ready → sent → archived).

### Tests (write FIRST, must FAIL)

- [x] T051 Write unit tests for communication database operations in backend/tests/unit/test_database.py: create_communication (with contact_name denormalization), load_communications(app_id) sorted by date desc, update_communication (including status changes), delete_communication
- [x] T052 [P] Write contract tests for communication REST API in backend/tests/contract/test_rest_api.py: GET/POST /api/applications/{id}/communications, PUT/DELETE /api/applications/{id}/communications/{comm_id}
- [x] T053 [P] Write contract tests for communication MCP tools in backend/tests/contract/test_write_tools.py: add_communication, update_communication, remove_communication

### Implementation

- [x] T054 Implement communication database operations in backend/src/persona/database.py: create_communication(app_id, data) with contact_name auto-population from contact_id, load_communications(app_id), update_communication(id, data), delete_communication(id)
- [x] T055 Add communication methods to ApplicationService in backend/src/persona/application_service.py: add_communication, list_communications, update_communication, remove_communication
- [x] T056 Add communication REST routes to backend/src/persona/api/routes.py: GET/POST /api/applications/{id}/communications, PUT/DELETE /api/applications/{id}/communications/{comm_id}
- [x] T057 Add communication MCP tools to backend/src/persona/tools/application_tools.py: add_communication, update_communication, remove_communication
- [x] T058 [P] Add communication TypeScript types to frontend/src/types/resume.ts: Communication interface (id, app_id, contact_id, contact_name, type, direction, subject, body, date, status, created_at)
- [x] T059 Add communication API calls to frontend/src/services/api.ts: listCommunications(appId), addCommunication(appId, data), updateCommunication(appId, commId, data), removeCommunication(appId, commId)
- [x] T060 Create frontend/src/components/CommunicationsPanel.tsx: reverse-chronological timeline of communications with status badges (draft/ready/sent/archived). Add communication form. Status transition buttons. Used within ApplicationDetailView.
- [x] T061 Integrate CommunicationsPanel into frontend/src/components/ApplicationDetailView.tsx

**Checkpoint**: Communication tracking works for all applications. Status workflow (draft→ready→sent→archived) functional. `make check` passes.

---

## Phase 7: User Story 5 — AI-Assisted Communication Drafting & Context (Priority: P5)

**Goal**: AI assistants can read full application context and draft communications stored as draft entries.

**Independent Test**: Call get_application_context MCP tool, verify it returns application + contacts + communications + resume versions. AI can store a draft communication.

### Tests (write FIRST, must FAIL)

- [x] T062 Write contract tests for get_application_context MCP tool in backend/tests/contract/test_read_tools.py: returns application, contacts, communications, resume_version (associated), default_resume. Test with and without associated resume version.
- [x] T063 [P] Write contract test for get_application_context REST endpoint in backend/tests/contract/test_rest_api.py: GET /api/applications/{id}/context
- [x] T064 [P] Write integration test in backend/tests/integration/test_cross_interface.py: create application via REST, add contacts and communications via MCP, read context via MCP, verify all data consistent. Test AI draft workflow: create draft communication via MCP with status="draft", verify it appears in REST communication list.

### Implementation

- [x] T065 Add get_application_context method to ApplicationService in backend/src/persona/application_service.py: loads application, contacts, communications, associated resume version (if any), and default resume version. Returns composite dict.
- [x] T066 Add GET /api/applications/{id}/context REST route to backend/src/persona/api/routes.py
- [x] T067 Add get_application_context MCP tool to backend/src/persona/tools/application_tools.py

**Checkpoint**: AI context tool works. Full end-to-end flow: create app, add data, get context, store draft. `make check` passes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and cleanup

- [x] T068 Write cross-interface integration tests in backend/tests/integration/test_cross_interface.py: resume version operations consistent across REST and MCP. Application cascade delete verified across interfaces. Default resume invariant maintained across operations.
- [x] T069 [P] Update backend/tests/integration/test_server.py for new server structure (tools split into modules, new routes)
- [x] T070 [P] Update frontend component tests to cover navigation between Resumes and Applications views
- [x] T071 Update README.md to reflect new capabilities: multi-resume management, job application tracking, MCP tool changes, REST API changes, UI changes per constitution requirement
- [x] T072 Run quickstart.md validation scenarios end-to-end and fix any issues
- [x] T073 Run `make check` at root level to verify all backend and frontend tests pass, linting clean

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories (migration replaces entire resume layer)
- **Phase 3 (US4 Resumes)**: Depends on Phase 2 — must complete before Phase 4 (apps reference resume versions)
- **Phase 4 (US1 Applications)**: Depends on Phase 3 — applications reference resume versions via FK
- **Phase 5 (US2 Contacts)**: Depends on Phase 4 — contacts belong to applications
- **Phase 6 (US3 Communications)**: Depends on Phase 5 — communications can reference contacts
- **Phase 7 (US5 AI Context)**: Depends on Phases 4, 5, 6 — context aggregates all entities
- **Phase 8 (Polish)**: Depends on all previous phases

### User Story Dependencies

```
Phase 2 (Foundation)
  └── Phase 3: US4 Resumes (replaces old resume system)
       └── Phase 4: US1 Applications (apps reference resume versions)
            ├── Phase 5: US2 Contacts (contacts belong to apps)
            │    └── Phase 6: US3 Communications (comms can ref contacts)
            │         └── Phase 7: US5 AI Context (aggregates all)
            └── Phase 7: US5 AI Context (needs apps at minimum)
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation (TDD per constitution)
2. Database operations before service layer
3. Service layer before REST routes and MCP tools
4. Backend before frontend
5. Core implementation before integration

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:
- T003/T004/T005: Empty module creation
- T007/T008: Unit test writing (different test files)
- T014: MCP contract tests alongside T013 REST contract tests
- T026/T027: Application contract tests (REST and MCP)
- T041/T042: Contact contract tests
- T052/T053: Communication contract tests
- T063/T064: Context endpoint tests
- T069/T070: Integration test updates

---

## Parallel Example: Phase 4 (User Story 1)

```bash
# Write tests in parallel:
Task T024: "Unit tests for application DB operations"
Task T025: "Unit tests for ApplicationService"
Task T026: "Contract tests for application REST API"
Task T027: "Contract tests for application MCP tools"

# After tests, implement sequentially:
Task T028: "Application database operations"
Task T029: "ApplicationService implementation"
Task T030: "Application REST routes" # depends on T029
Task T031: "Application MCP tools"   # depends on T029

# Frontend in parallel after backend:
Task T033: "Application TypeScript types"
Task T034: "Application API calls"   # depends on T033
Task T035: "ApplicationListView"     # depends on T034
Task T036: "ApplicationDetailView"   # depends on T034
```

---

## Implementation Strategy

### MVP First (Phases 1-4: Resume Versions + Applications)

1. Complete Phase 1: Setup (empty modules)
2. Complete Phase 2: Migration + resume version core (CRITICAL)
3. Complete Phase 3: US4 Resume version management (replaces old system)
4. Complete Phase 4: US1 Application CRUD
5. **STOP and VALIDATE**: Resume versions work, applications work, old API replaced
6. Deploy/demo as MVP

### Incremental Delivery

1. Phases 1-3 → Resume version management works (existing functionality preserved + enhanced)
2. + Phase 4 → Application tracking works
3. + Phase 5 → Contact management works
4. + Phase 6 → Communication tracking works
5. + Phase 7 → AI context access works
6. + Phase 8 → Polish, docs, final validation

Each phase adds value without breaking previous phases.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- US4 (Resumes) is implemented before US1 (Applications) because applications depend on resume versions
- Constitution requires TDD: write failing tests before implementation code
- Each checkpoint should pass `make check` before proceeding
- Commit after each task or logical group
