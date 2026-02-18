# Implementation Plan: Job Application Management (rev 3)

**Branch**: `006-job-applications` | **Date**: 2026-02-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-job-applications/spec.md`

## Summary

Add job application tracking with contacts, communications, and multi-resume management to the persona system. The existing singleton resume is replaced by a list of resume versions (one marked as default). All resume editing capabilities work on every version. Applications can be associated with resume versions. AI assistants access full context via MCP for resume tailoring and communication drafting. Delivered through MCP tools, REST API, and web UI.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastMCP >=2.3.0, FastAPI >=0.100.0, React 18, Vite 6
**Storage**: SQLite via stdlib sqlite3 with DBConnection protocol
**Testing**: pytest (backend), Vitest with React Testing Library (frontend)
**Target Platform**: Linux/macOS server, web browser
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 100+ applications without degradation in list views
**Constraints**: Single-user, personal tool. No auth. Minimal dependencies per constitution.
**Scale/Scope**: Single user, hundreds of applications, dozens of resume versions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | All resume + application features exposed as MCP tools |
| II. Single-Package Distribution | PASS | No new packages needed; same uvx entry point |
| III. Test-Driven Development | PASS | TDD required: tests before implementation for all new tools and endpoints |
| IV. Minimal Dependencies | PASS | No new dependencies needed. JSON blob approach uses stdlib json. State-based navigation avoids React Router. |
| V. Explicit Error Handling | PASS | All MCP tools return structured errors. REST routes use HTTPException with appropriate status codes. |

**Post-design re-check**: All gates still pass. JSON blob storage uses stdlib. No new deps introduced.

## Project Structure

### Documentation (this feature)

```text
specs/006-job-applications/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── rest-api.md      # REST API contracts
│   └── mcp-tools.md     # MCP tool contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/persona/
│   ├── server.py             # FastAPI + MCP server (updated: new MCP tools, resume version-aware)
│   ├── models.py             # Pydantic models (updated: add ResumeVersion, Application, etc.)
│   ├── database.py           # SQLite operations (updated: resume version CRUD, application CRUD)
│   ├── db.py                 # DBConnection protocol (unchanged)
│   ├── config.py             # Configuration (unchanged)
│   ├── migrations.py         # Schema migrations (updated: v1→v2 migration)
│   ├── resume_service.py     # Resume business logic (updated: version-aware operations)
│   ├── application_service.py # NEW: Application CRUD business logic
│   ├── api/
│   │   └── routes.py         # REST routes (updated: /api/resumes/*, /api/applications/*)
│   └── tools/                # NEW: MCP tool handlers split by domain
│       ├── resume_tools.py   # Resume version MCP tools
│       └── application_tools.py # Application MCP tools
└── tests/
    ├── conftest.py           # Shared fixtures (updated)
    ├── unit/
    │   ├── test_models.py            # Model validation tests (updated)
    │   ├── test_database.py          # DB operation tests (updated: version-aware)
    │   ├── test_migrations.py        # Migration tests (updated: v1→v2)
    │   ├── test_resume_service.py    # Resume service tests (updated: version-aware)
    │   └── test_application_service.py # NEW: Application service tests
    ├── contract/
    │   ├── test_rest_api.py          # REST API tests (updated: new routes)
    │   ├── test_read_tools.py        # MCP read tool tests (updated)
    │   └── test_write_tools.py       # MCP write tool tests (updated)
    └── integration/
        ├── test_cross_interface.py   # Cross-interface tests (updated)
        └── test_server.py            # Server integration tests (updated)

frontend/
├── src/
│   ├── App.tsx               # Root component (updated: navigation, multiple views)
│   ├── components/
│   │   ├── Navigation.tsx          # NEW: Top-level nav bar
│   │   ├── ResumeListView.tsx      # NEW: Resume versions list (replaces ResumeView entry point)
│   │   ├── ResumeDetailView.tsx    # NEW: Single resume version editor (reuses section components)
│   │   ├── ContactSection.tsx      # Updated: accepts version ID for API calls
│   │   ├── SummarySection.tsx      # Updated: accepts version ID for API calls
│   │   ├── ExperienceSection.tsx   # Updated: accepts version ID for API calls
│   │   ├── EducationSection.tsx    # Updated: accepts version ID for API calls
│   │   ├── SkillsSection.tsx       # Updated: accepts version ID for API calls
│   │   ├── ApplicationListView.tsx # NEW: Applications list with filter/search
│   │   ├── ApplicationDetailView.tsx # NEW: Application detail with contacts, comms
│   │   ├── ContactsPanel.tsx       # NEW: Application contacts sub-panel
│   │   ├── CommunicationsPanel.tsx # NEW: Application communications timeline
│   │   ├── EditableSection.tsx     # Unchanged
│   │   ├── EntryForm.tsx           # Unchanged
│   │   ├── ConfirmDialog.tsx       # Unchanged
│   │   ├── LoadingSpinner.tsx      # Unchanged
│   │   └── StatusMessage.tsx       # Unchanged
│   ├── services/
│   │   └── api.ts            # API client (updated: version-scoped resume calls, application calls)
│   └── types/
│       └── resume.ts         # TypeScript types (updated: ResumeVersion, Application, etc.)
└── src/__tests__/            # Component tests (updated + new)
```

**Structure Decision**: Web application pattern (backend/ + frontend/) — matches existing project structure. MCP tool handlers split into separate files by domain (resume vs application) for clarity. New ApplicationService parallels existing ResumeService pattern.

## Design Decisions

### 1. JSON Blob for Resume Version Data

Resume versions store the full resume as a serialized JSON blob in `resume_data TEXT`. Section-level editing deserializes → mutates → reserializes. This avoids duplicating 5 tables and keeps versions self-contained.

### 2. Migration Strategy (v1 → v2)

The migration reads existing singleton data (contact, summary, experience, education, skill tables), builds a Resume model, serializes to JSON, inserts as the first resume version (is_default=1, label="Default Resume"), then drops the old tables.

### 3. MCP Tool Organization

Tools split into two files: `tools/resume_tools.py` and `tools/application_tools.py`. Each registers tools on the shared FastMCP instance. This keeps server.py clean.

### 4. Frontend Navigation

State-based navigation (no React Router). A `Navigation` component switches between views: Resumes list, Resume detail, Applications list, Application detail. This avoids a new dependency.

### 5. Section Components Reuse

Existing section components (ContactSection, SummarySection, etc.) gain a `versionId` prop and call version-scoped API endpoints (`/api/resumes/{id}/contact` etc.). Same editing UX, different data scope.

### 6. Default Resume Convenience

Both REST (`GET /api/resumes/default`) and MCP (`get_resume()` with no id) support getting the default resume without knowing its ID. This preserves the simple "get my resume" workflow.

### 7. Application Context for AI

The `get_application_context` tool/endpoint returns both the associated resume version and the default resume, giving AI assistants full context for both tailoring and communication drafting.

## Implementation Phases

### Phase 1: Foundation (Schema + Migration + Resume Versions)

1. Update migrations.py with v1→v2 migration
2. Update models.py with new Pydantic models (ResumeVersion, Application, etc.)
3. Update database.py with resume version CRUD (JSON blob read/write)
4. Update resume_service.py to be version-aware
5. Update REST routes for `/api/resumes/*`
6. Update MCP tools for resume versions
7. Tests at each layer (TDD)

### Phase 2: Applications + Contacts + Communications

1. Add application_service.py with application CRUD
2. Add database operations for applications, contacts, communications
3. Add REST routes for `/api/applications/*`
4. Add MCP tools for applications
5. Tests at each layer (TDD)

### Phase 3: AI Context + Cross-cutting

1. Implement `get_application_context` composite endpoint/tool
2. Cross-interface integration tests
3. Frontend navigation + resume version management UI
4. Frontend application management UI

### Phase 4: Polish

1. Frontend styling and UX polish
2. README updates
3. Final integration testing
