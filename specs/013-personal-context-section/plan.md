# Implementation Plan: Personal Context Notes

**Branch**: `013-personal-context-section` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/013-personal-context-section/spec.md`

## Summary

Add personal notes management as a new "Notes" section alongside the existing "Jobs" section. Notes are a standalone entity stored in a new PostgreSQL table (schema v5→v6 migration) with title (required), content (optional), and free-form tags (JSON array, lowercased). The feature is exposed through all three interfaces: REST API (`/api/notes`), MCP server (5 new tools), and a React UI section. Tags support autocomplete from a unified pool (notes + accomplishments merged client-side). List ordering is reverse-chronological by last-modified timestamp. Keyword search supports multi-word AND matching with case-insensitive substring matching. No new third-party dependencies are required.

See [research.md](research.md) for all design decisions and [data-model.md](data-model.md) for schema, models, and service signatures.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastMCP >=2.3.0, FastAPI >=0.100.0, React 18, Vite 6 (all existing — no new deps)
**Storage**: PostgreSQL 16+, schema v5 → v6 migration
**Testing**: pytest (backend unit + contract + integration), Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browser (React SPA)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Perceived-immediate response (under 500ms) for a single authenticated user; dataset of up to 500 notes
**Constraints**: No new third-party dependencies (Constitution IV); TDD red-green-refactor mandatory (Constitution III)
**Scale/Scope**: Single-user personal tool; no concurrency concerns beyond last-write-wins

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | ✅ PASS | 5 MCP tools registered: `list_notes` (with `q` and `tag` params for search/filter), `get_note`, `create_note`, `update_note`, `delete_note`. All return structured responses or structured errors. |
| II. Single-Package Distribution | ✅ PASS | No new packages. All new code is in the existing `persona` package. |
| III. Test-Driven Development | ✅ PASS | Tests are written before implementation in task order. Every MCP tool has a contract test. |
| IV. Minimal Dependencies | ✅ PASS | Zero new third-party dependencies. JSON array stored as TEXT (stdlib `json`). Search uses PostgreSQL ILIKE. |
| V. Explicit Error Handling | ✅ PASS | `ValueError` at service layer → `HTTPException` (422/404) at route layer. MCP tools catch `ValueError` and return structured error strings. `PermissionError` → 403. |

**Constitution Check post-design**: All gates pass. The standalone `note` table (FK to `users` only) is the simplest model and follows the established accomplishments pattern exactly. No complexity justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/013-personal-context-section/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: design decisions
├── data-model.md        # Phase 1: schema, models, service signatures
├── quickstart.md        # Phase 1: run & test guide
├── contracts/
│   └── notes.yaml       # Phase 1: OpenAPI 3.0 contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code

```text
backend/
├── src/persona/
│   ├── migrations.py              [MOD] Add migrate_v5_to_v6(); append to MIGRATIONS list
│   ├── models.py                  [MOD] Add Note, NoteSummary models
│   ├── database.py                [MOD] Add note CRUD functions + helpers
│   ├── note_service.py            [NEW] NoteService class (validation, tag normalization)
│   ├── api/
│   │   └── routes.py              [MOD] Add note_service param + note routes (6 endpoints)
│   ├── tools/
│   │   └── note_tools.py          [NEW] register_note_tools() (6 MCP tools)
│   └── server.py                  [MOD] Wire NoteService; register MCP tools; pass to create_router
└── tests/
    ├── unit/
    │   └── test_note_service.py   [NEW] Service + DB unit tests
    ├── contract/
    │   └── test_note_api.py       [NEW] REST + MCP contract tests
    └── integration/
        └── test_cross_interface.py  [MOD] Add note cross-interface tests

frontend/
├── src/
│   ├── types/
│   │   └── resume.ts              [MOD] Add Note, NoteSummary interfaces
│   ├── services/
│   │   └── api.ts                 [MOD] Add note API functions (6 functions)
│   ├── components/
│   │   ├── NoteListView.tsx       [NEW] List with search + tag filter + new form
│   │   └── NoteDetailView.tsx     [NEW] Detail view + inline edit form
│   ├── router.tsx                 [MOD] Add /notes and /notes/:id routes
│   └── App.tsx                    [MOD] Add Notes nav tab
└── src/__tests__/
    └── components/
        ├── NoteListView.test.tsx  [NEW]
        └── NoteDetailView.test.tsx [NEW]

README.md                           [MOD] Document notes feature
```

**Structure Decision**: Web application (frontend + backend). The feature follows the established layered architecture: PostgreSQL DB functions → Service class → (REST routes + MCP tools) → React components. No new layers or abstractions are introduced. The pattern mirrors accomplishments (007) exactly.

## Complexity Tracking

*No constitution violations. This table is not applicable.*
