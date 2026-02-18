# Implementation Plan: Accomplishments Management

**Branch**: `feat-007-accomplishments` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/007-accomplishments/spec.md`

## Summary

Add full CRUD management for career accomplishments using the STAR storytelling format (Situation, Task, Action, Result). Accomplishments are a standalone entity stored in a new SQLite table (schema v2→v3 migration). The feature is exposed through all three existing surfaces: REST API (`/api/accomplishments`), MCP server (5 new tools), and a React UI section. Tags support autocomplete from previously-used values. List ordering is reverse-chronological by user-editable accomplishment date. No new third-party dependencies are required.

See [research.md](research.md) for all design decisions and [data-model.md](data-model.md) for schema, models, and service signatures.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastMCP >=2.3.0, FastAPI >=0.100.0, React 18, Vite 6 (all existing — no new deps)
**Storage**: SQLite via stdlib `sqlite3`, schema v2 → v3 migration
**Testing**: pytest (backend unit + contract + integration), Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browser (React SPA)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Perceived-immediate response for a single authenticated user; small dataset (dozens to hundreds of accomplishments)
**Constraints**: No new third-party dependencies (Constitution IV); TDD red-green-refactor mandatory (Constitution III)
**Scale/Scope**: Single-user personal tool; no concurrency or multi-tenancy concerns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | ✅ PASS | 5 MCP tools registered: `list_accomplishments`, `get_accomplishment`, `create_accomplishment`, `update_accomplishment`, `delete_accomplishment`. All return structured responses or structured errors. |
| II. Single-Package Distribution | ✅ PASS | No new packages. All new code is in the existing `persona` package. |
| III. Test-Driven Development | ✅ PASS | Tests are written before implementation in task order. Every MCP tool has a contract test. |
| IV. Minimal Dependencies | ✅ PASS | Zero new third-party dependencies. JSON array stored as TEXT (stdlib `json`). |
| V. Explicit Error Handling | ✅ PASS | `ValueError` at service layer → `HTTPException` (422/404) at route layer. MCP tools catch `ValueError` and return structured error strings. |

**Constitution Check post-design**: All gates pass. The standalone `accomplishment` table (no FK to `resume_version`) is the simplest model for a personal tool and does not require a complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/007-accomplishments/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: design decisions
├── data-model.md        # Phase 1: schema, models, service signatures
├── quickstart.md        # Phase 1: run & test guide
├── contracts/
│   └── accomplishments.yaml  # Phase 1: OpenAPI 3.0 contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code

```text
backend/
├── src/persona/
│   ├── migrations.py           [MOD] Add migrate_v2_to_v3(); append to MIGRATIONS list
│   ├── models.py               [MOD] Add Accomplishment, AccomplishmentSummary models
│   ├── accomplishment_service.py  [NEW] AccomplishmentService class
│   ├── api/
│   │   └── routes.py           [MOD] Add acc_service param + accomplishment routes
│   ├── tools/
│   │   └── accomplishment_tools.py  [NEW] register_accomplishment_tools()
│   └── server.py               [MOD] Wire AccomplishmentService; register MCP tools
└── tests/
    ├── unit/
    │   └── test_accomplishment_service.py  [NEW] Service + DB unit tests
    ├── contract/
    │   └── test_accomplishment_api.py      [NEW] REST contract tests
    └── integration/
        └── test_cross_interface.py         [MOD] Add accomplishment cross-interface tests

frontend/
├── src/
│   ├── types/
│   │   └── resume.ts                    [MOD] Add Accomplishment, AccomplishmentSummary interfaces
│   ├── services/
│   │   └── api.ts                       [MOD] Add accomplishment API functions (6 functions)
│   ├── components/
│   │   ├── AccomplishmentListView.tsx   [NEW] List with tag filter + new form
│   │   └── AccomplishmentDetailView.tsx [NEW] Detail view + inline edit form
│   └── App.tsx                          [MOD] Add Accomplishments section/tab
└── src/__tests__/
    └── components/
        ├── AccomplishmentListView.test.tsx   [NEW]
        └── AccomplishmentDetailView.test.tsx [NEW]

README.md                                 [MOD] Document accomplishments feature
```

**Structure Decision**: Web application (Option 2 from template). The feature follows the established layered architecture: SQLite DB functions → Service class → (REST routes + MCP tools) → React components. No new layers or abstractions are introduced.

## Complexity Tracking

*No constitution violations. This table is not applicable.*
