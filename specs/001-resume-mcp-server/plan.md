# Implementation Plan: Persona MCP Server with Resume Tools

**Branch**: `feature/001-resume-mcp-server` | **Date**: 2026-02-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-resume-mcp-server/spec.md`

## Summary

Build a Python MCP server ("persona") that reads and writes resume data from a local Markdown file with YAML front-matter. The server exposes MCP tools for retrieving and modifying resume sections (contact info, summary, experience, education, skills). It uses the official `mcp` Python SDK with FastMCP, stores data in `~/.persona/jobs/resume/resume.md` (configurable via `PERSONA_DATA_DIR`), and is distributed as a single `uvx`-installable package.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `mcp` (official Python MCP SDK, provides FastMCP), `python-frontmatter` (Markdown+YAML parsing)
**Storage**: Local filesystem — single Markdown file with YAML front-matter (`jobs/resume/resume.md`)
**Testing**: `pytest` with `pytest-asyncio`
**Type Checking**: `pyright` (must pass with no errors per constitution)
**Target Platform**: Local machine (macOS/Linux), STDIO transport
**Project Type**: Single package (src-layout)
**Performance Goals**: <2s for any read or write operation, <2s server startup (per SC-001, SC-003)
**Constraints**: Single-user, local-only, no network dependencies at runtime
**Scale/Scope**: Single resume file with up to 50 entries across all sections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | All functionality exposed via MCP tools using FastMCP. STDIO transport. Lifecycle methods handled by SDK. |
| II. Single-Package Distribution via uvx | PASS | `pyproject.toml` with `[project.scripts]` entry point `persona`. Installable via `uvx persona`. |
| III. Test-Driven Development (TDD) | PASS | Contract tests for every tool (input schema, output schema, error behavior). `pytest` + `pytest-asyncio`. Red-Green-Refactor workflow. |
| IV. Minimal Dependencies | PASS | Only 2 runtime deps: `mcp` (required, no justification needed per constitution) and `python-frontmatter` (justified: zero-dep library solving exact problem, no stdlib alternative). |
| V. Explicit Error Handling | PASS | `ToolError` at handler boundary. Structured messages. No stack traces to clients. |
| Type Checking | PASS | `pyright` in dev dependencies. `make typecheck` target runs `uv run pyright`. Must pass with no errors. |
| Makefile targets | PASS | `make run`, `make test`, `make lint`, `make typecheck`, `make check` all defined. |
| Branching/Commits | PASS | `feature/001-resume-mcp-server` branch. Conventional commits. |

**Post-Phase 1 Re-check**: All gates still pass. No new dependencies introduced. Tool contracts align with MCP protocol. Data model uses file storage as specified.

## Project Structure

### Documentation (this feature)

```text
specs/001-resume-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── mcp-tools.md    # MCP tool input/output schemas
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
└── persona/
    ├── __init__.py          # Package init, version
    ├── server.py            # FastMCP server setup, entry point
    ├── config.py            # Data directory resolution, env var handling
    ├── models.py            # Pydantic models (ContactInfo, WorkExperience, etc.)
    ├── resume_store.py      # File I/O: read/write resume.md via python-frontmatter
    └── tools/
        ├── __init__.py
        ├── read.py          # get_resume, get_resume_section
        └── write.py         # update_section, add_entry, update_entry, remove_entry

tests/
├── conftest.py              # Shared fixtures (tmp data dir, sample resume.md)
├── contract/
│   ├── test_read_tools.py   # Contract tests for P1 read tools
│   └── test_write_tools.py  # Contract tests for P2 write tools
├── unit/
│   ├── test_config.py       # Config resolution tests
│   ├── test_models.py       # Pydantic model validation tests
│   └── test_resume_store.py # File I/O parsing and writing tests
└── integration/
    └── test_server.py       # End-to-end server startup and tool invocation

pyproject.toml               # Package metadata, dependencies, entry point
Makefile                     # make run, make test, make lint, make typecheck, make check
```

**Structure Decision**: Single-package src-layout (`src/persona/`). This is a CLI tool with no frontend or API server component. The `tools/` subdirectory separates read and write tool handlers to support the spec's P1/P2 priority split and future tool expansion.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
