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
