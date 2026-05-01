# Implementation Plan: Improved Tags Handling

**Branch**: `feat-015-tags-handling` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)

## Summary

Replace comma-separated plain text tag inputs with a chip-based `TagInput` component that features autocomplete, Enter/comma commit, per-chip removal, "Create new tag" option, and lowercase normalization. Upgrade list-view tag filters from single-select `<select>` to multi-select chip UI with server-side AND logic. Backend: fix tag normalization inconsistency in AccomplishmentService and extend list endpoints to accept multiple `tag` query parameters.

## Technical Context

**Language/Version**: Python 3.11+ (backend); TypeScript 5.x / React 18 (frontend)  
**Primary Dependencies**: FastAPI ≥0.100.0, FastMCP ≥2.3.0 (backend); React 18, Vite 6, Vitest 2 (frontend) — all existing, no new deps  
**Storage**: PostgreSQL 16+ — no schema changes  
**Testing**: pytest (backend); Vitest + React Testing Library (frontend)  
**Target Platform**: Web (served by FastAPI static file serving)  
**Project Type**: Web application (backend/ + frontend/)  
**Performance Goals**: Standard web app responsiveness; autocomplete dropdown renders on each keystroke without noticeable lag  
**Constraints**: No new frontend or backend dependencies (Constitution IV). No schema migrations.  
**Scale/Scope**: Single-user context; tag pool derived at runtime from existing records

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| I. MCP Protocol Compliance | Pass | No MCP tool changes; feature is UI + REST only |
| II. Single-Package Distribution (uvx) | Pass | No new packages; no pyproject.toml changes |
| III. TDD — tests before implementation | **Required** | All new code must follow Red-Green-Refactor. See quickstart.md Step order. |
| IV. Minimal Dependencies | Pass | No new deps. Custom TagInput instead of react-select/downshift. |
| V. Explicit Error Handling | Pass | No new MCP tools; existing error handling unchanged |

No violations. No Complexity Tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/015-tags-handling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── backend-api.md
│   └── frontend-component.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code

```text
backend/
├── src/persona/
│   ├── accomplishment_service.py   # _normalize_tags: add lowercase; list_accomplishments: tags[]
│   ├── note_service.py             # list_notes: tags[]
│   ├── database.py                 # load_accomplishments / load_notes: tags[] + AND logic
│   └── api/
│       └── routes.py               # tag: list[str] | None = Query(default=None)
└── tests/
    ├── unit/
    │   ├── test_accomplishment_service.py   # Add/update tag normalization + multi-tag filter tests
    │   └── test_note_service.py             # Add multi-tag filter tests
    └── contract/
        ├── test_accomplishment_api.py        # Add multi-tag REST tests
        └── test_note_api.py                  # Add multi-tag REST tests

frontend/
├── src/
│   ├── components/
│   │   ├── TagInput.tsx                      # NEW: shared chip input component
│   │   ├── TagInput.module.css               # NEW
│   │   ├── AccomplishmentListView.tsx        # Use TagInput for form tags + filter
│   │   ├── NoteListView.tsx                  # Use TagInput for form tags + filter
│   │   ├── AccomplishmentDetailView.tsx      # Use TagInput for edit form tags
│   │   └── NoteDetailView.tsx               # Use TagInput for edit form tags
│   └── services/
│       └── api.ts                            # listAccomplishments/listNotes: tags?: string[]
└── src/__tests__/components/
    ├── TagInput.test.tsx                     # NEW: component tests
    ├── AccomplishmentListView.test.tsx       # Update tag assertions
    ├── NoteListView.test.tsx                 # Update tag assertions
    ├── AccomplishmentDetailView.test.tsx     # Update tag assertions
    └── NoteDetailView.test.tsx              # Update tag assertions
```

**Structure Decision**: Web application (Option 2 from template). Backend and frontend are separate directories under the repo root. No new directories needed.
