# Implementation Plan: SQLite Storage

**Branch**: `feat-003-sqlite` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-sqlite/spec.md`

## Summary

Replace the markdown file-based resume storage (`resume_store.py` + `python-frontmatter`) with a SQLite database using Python's stdlib `sqlite3` module. The 6 existing MCP tool signatures are preserved — only the storage layer changes. Includes a lightweight schema migration framework using `PRAGMA user_version` for automatic, transactional, forward-only schema upgrades on startup.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `mcp` (MCP SDK), `sqlite3` (stdlib — replaces `python-frontmatter`)
**Storage**: SQLite via stdlib `sqlite3`, database file at `{data_dir}/persona.db`
**Testing**: `pytest` with `pytest-asyncio`, in-memory SQLite databases for isolation
**Target Platform**: Cross-platform (macOS, Linux) — distributed via `uvx`
**Project Type**: Single package
**Performance Goals**: System starts and is usable within 2 seconds (SC-003)
**Constraints**: Zero dependencies beyond `mcp`; single-user; no concurrent write concerns
**Scale/Scope**: 5 tables, 6 MCP tools, ~1 user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | Tool signatures preserved. All functionality exposed via MCP tools. |
| II. Single-Package Distribution via uvx | PASS | `sqlite3` is stdlib — no new PyPI dependencies. Removing `python-frontmatter` reduces dependency count. |
| III. Test-Driven Development | PASS | Plan follows TDD: tests written before implementation for each module. |
| IV. Minimal Dependencies | PASS | Net reduction: removing `python-frontmatter`, adding nothing. `sqlite3` is stdlib. |
| V. Explicit Error Handling | PASS | New error types (`SchemaVersionError`, `MigrationError`) with human-readable messages. All exceptions caught at tool handler boundary. |

**Post-Phase 1 Re-check**: All gates still pass. No new dependencies introduced. Migration framework uses only stdlib. Error handling for migration failures and version mismatches follows Principle V.

## Project Structure

### Documentation (this feature)

```text
specs/003-sqlite/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: SQLite schema design
├── quickstart.md        # Phase 1: implementation guide
├── contracts/
│   ├── mcp-tools.md     # Phase 1: MCP tool behavioral contracts
│   └── database.md      # Phase 1: database module interface contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/persona/
├── __init__.py
├── server.py            # MCP server entrypoint (MODIFIED: init DB, pass conn)
├── models.py            # Pydantic data models (UNCHANGED)
├── config.py            # Configuration (MODIFIED: add DB filename constant)
├── database.py          # NEW: SQLite CRUD operations
├── migrations.py        # NEW: Schema migration framework
├── resume_store.py      # REMOVED: replaced by database.py
└── tools/
    ├── __init__.py
    ├── read.py           # Read tool handlers (MODIFIED: use conn instead of data_dir)
    └── write.py          # Write tool handlers (MODIFIED: use conn instead of data_dir)

tests/
├── conftest.py          # MODIFIED: SQLite fixtures replace markdown fixtures
├── unit/
│   ├── test_config.py       # UNCHANGED
│   ├── test_models.py       # UNCHANGED
│   ├── test_database.py     # NEW: database CRUD tests
│   ├── test_migrations.py   # NEW: migration framework tests
│   └── test_resume_store.py # REMOVED
├── contract/
│   ├── test_read_tools.py   # MODIFIED: SQLite fixtures
│   └── test_write_tools.py  # MODIFIED: SQLite fixtures
└── integration/
    └── test_server.py       # MODIFIED: SQLite-based end-to-end
```

**Structure Decision**: Single project structure (existing). No new directories beyond the new source files. The `tools/` subdirectory pattern is preserved.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
