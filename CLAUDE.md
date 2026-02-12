# personal-mcp

Persona MCP Server — a Python MCP server for resume/personal data, installable via `uvx`.

## Constitution

All project principles, technology constraints, packaging rules, development workflow, and governance are defined in [`.specify/memory/constitution.md`](.specify/memory/constitution.md). That document is authoritative — read it before making changes.

## Quick Reference

```bash
make check    # lint + typecheck + test (run before committing)
make test     # uv run pytest
make lint     # ruff check + format check
make run      # uv run persona
make format   # auto-format with ruff
```

## Project Layout

```
src/persona/          # main package
  server.py           # MCP server entrypoint
  models.py           # data models
  config.py           # configuration
  resume_store.py     # resume data store
  tools/              # MCP tool handlers (read.py, write.py)
tests/
  unit/               # unit tests
  contract/           # MCP contract tests
  integration/        # integration tests
```

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## Active Technologies
- Python 3.11 (minimum supported per pyproject.toml) + GitHub Actions, `astral-sh/setup-uv` action (feature/002-ci-pipeline)
- Python 3.11+ + `mcp` (MCP SDK), `sqlite3` (stdlib — replaces `python-frontmatter`) (feat-003-sqlite)
- SQLite via stdlib `sqlite3`, database file at `{data_dir}/persona.db` (feat-003-sqlite)
- Python 3.11+ + FastMCP >=2.3.0, FastAPI >=0.100.0, uvicorn >=0.20.0 (feat-004-rest-api)
- SQLite via stdlib `sqlite3` (existing, unchanged) (feat-004-rest-api)
- Python 3.11+ + `fastmcp>=2.3.0`, `fastapi>=0.100.0`, `uvicorn>=0.20.0` (replaces `mcp>=1.0.0`) (feat-004-rest-api)
- SQLite via stdlib `sqlite3` (existing, unchanged) with `DBConnection` protocol for future DB swaps (feat-004-rest-api)

## Recent Changes
- feature/002-ci-pipeline: Added Python 3.11 (minimum supported per pyproject.toml) + GitHub Actions, `astral-sh/setup-uv` action
