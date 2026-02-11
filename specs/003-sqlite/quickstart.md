# Quickstart: SQLite Storage Implementation

**Feature**: feat-003-sqlite
**Date**: 2026-02-11

## What Changes

| Component | Before | After |
|-----------|--------|-------|
| Storage file | `~/.persona/jobs/resume/resume.md` | `~/.persona/persona.db` |
| Storage format | Markdown + YAML front-matter | SQLite database |
| Storage module | `persona.resume_store` | `persona.database` |
| Dependencies | `python-frontmatter` | (none — `sqlite3` is stdlib) |
| MCP tools | 6 tools | Same 6 tools, same signatures |

## What Stays the Same

- All MCP tool names, parameters, and return types.
- Pydantic models (`ContactInfo`, `WorkExperience`, `Education`, `Skill`, `Resume`).
- Configuration: `PERSONA_DATA_DIR` env var and `~/.persona` default.
- Test structure: `tests/unit/`, `tests/contract/`, `tests/integration/`.
- All existing Makefile targets.

## New Modules

### `src/persona/database.py`
Core database module. Handles:
- Connection creation and configuration (WAL mode, foreign keys)
- Schema migration (`PRAGMA user_version` based)
- All CRUD operations (replacing `resume_store.py`)

### `src/persona/migrations.py`
Migration definitions. Contains:
- Ordered list of migration functions
- `SCHEMA_VERSION` constant
- `apply_migrations()` orchestrator
- Custom exceptions: `SchemaVersionError`, `MigrationError`

## Files Modified

| File | Change |
|------|--------|
| `src/persona/server.py` | Replace `resume_store` imports with `database` module. Initialize DB connection in `main()`. |
| `src/persona/tools/read.py` | Accept `conn` instead of `data_dir`. Call `database` functions instead of `resume_store`. |
| `src/persona/tools/write.py` | Accept `conn` instead of `data_dir`. Call `database` functions instead of `resume_store`. |
| `src/persona/config.py` | Minor: DB file path constant (`PERSONA_DB_FILENAME = "persona.db"`). |
| `pyproject.toml` | Remove `python-frontmatter` dependency. |

## Files Removed

| File | Reason |
|------|--------|
| `src/persona/resume_store.py` | Replaced entirely by `database.py` |

## Files Added

| File | Purpose |
|------|---------|
| `src/persona/database.py` | SQLite CRUD operations |
| `src/persona/migrations.py` | Schema migration framework |
| `tests/unit/test_database.py` | Unit tests for database CRUD |
| `tests/unit/test_migrations.py` | Unit tests for migration framework |

## Development Sequence

1. **Write migration framework + tests** (TDD: `test_migrations.py` → `migrations.py`)
2. **Write database CRUD + tests** (TDD: `test_database.py` → `database.py`)
3. **Update tool handlers** to use new database module
4. **Update contract tests** to use SQLite fixtures instead of markdown fixtures
5. **Update integration tests** for end-to-end validation
6. **Update server.py** — wire DB initialization into startup
7. **Remove old code** — delete `resume_store.py`, remove `python-frontmatter` dependency
8. **Run `make check`** — verify everything passes

## Key Commands

```bash
make test       # Run all tests
make check      # Lint + typecheck + test (must pass before commit)
make run        # Start server (will auto-create DB)
```
