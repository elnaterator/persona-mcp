<!--
Sync Impact Report
===================
- Version change: 1.3.0 → 1.4.0
- Modified principles: None
- Added sections: None
- Removed sections: None
- Modified sections:
  - Development Workflow > General Workflow > Branching: switched from
    in-repo `git checkout -b` to `git worktree add` workflow for parallel
    feature development. Branch creation is now the developer's
    responsibility via git worktree; spec-kit scripts only create spec
    directories and files. Changed branch naming convention from
    `feature/<NNN>-<name>` to `feat-<NNN>-<name>` to avoid `/` in
    branch names which simplifies worktree directory management.
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed (generic)
  - .specify/templates/spec-template.md ✅ no changes needed (generic)
  - .specify/templates/tasks-template.md ✅ no changes needed (generic)
- Scripts requiring updates:
  - .specify/scripts/bash/create-new-feature.sh ✅ removed git checkout -b
- Follow-up TODOs: None
-->

# Personal MCP Server Constitution

## Core Principles

### I. MCP Protocol Compliance

All server functionality MUST be exposed through the Model Context
Protocol (MCP). Tools, resources, and prompts MUST conform to the
MCP specification. The server MUST handle MCP lifecycle methods
(initialize, ping, shutdown) correctly. Non-compliant endpoints
or side-channel communication methods are prohibited.

### II. Single-Package Distribution via uvx

The project MUST be installable and runnable via `uvx` as a single
command (e.g., `uvx personal-mcp`). The package MUST be published
to PyPI (or a configured index) as a standard Python package with
a `pyproject.toml` entry point. All dependencies MUST be declared
in `pyproject.toml` under `[project.dependencies]`. Vendoring or
requiring manual dependency installation is prohibited.

### III. Test-Driven Development (TDD)

Tests MUST be written before implementation code for all new tools,
resources, and prompts. The Red-Green-Refactor cycle is mandatory:
write a failing test, implement until it passes, then refactor.
Every MCP tool MUST have at least one contract test verifying its
input schema, output schema, and error behavior. `pytest` is the
required test runner.

**Test quality and maintainability rules:**

- Tests MUST be human-readable: a developer unfamiliar with the
  codebase MUST be able to understand what is being tested and why
  by reading the test name and body alone.
- Test helper functions MUST be used to eliminate repetitive setup,
  assertion patterns, or fixture construction when doing so improves
  readability. Helpers MUST have descriptive names that convey intent
  (e.g., `make_tool_request(...)`, `assert_error_response(...)`).
- Tests MUST be actively reviewed for refactoring opportunities:
  merge tests that verify the same logical behavior, consolidate
  overlapping parametrized cases, and remove redundant assertions.
- Test bloat is prohibited: each test MUST justify its existence by
  covering a distinct behavior or edge case. Two tests that differ
  only by a trivial input variation MUST be merged into a single
  parametrized test.
- Over-engineering in tests is prohibited: do not introduce test
  abstractions, base classes, or frameworks beyond simple helpers.
  Prefer flat, linear test functions over deeply nested or
  inheritance-based test structures.

### IV. Minimal Dependencies

Every third-party dependency MUST justify its inclusion. Prefer
the Python standard library when it provides equivalent
functionality. The MCP SDK (`mcp`) is the only framework-level
dependency permitted without justification. New dependencies MUST
be reviewed for maintenance status, license compatibility (MIT,
Apache-2.0, BSD), and transitive dependency footprint.

### V. Explicit Error Handling

All MCP tool handlers MUST return structured error responses rather
than raising unhandled exceptions. Errors MUST include a
human-readable message and, where applicable, a machine-readable
error code. Internal exceptions MUST be caught at the tool handler
boundary and translated into MCP error responses. Stack traces
MUST NOT be exposed to MCP clients in production.

## Technology & Packaging Constraints

- **Language**: Python 3.11+
- **MCP SDK**: `mcp` (official Python SDK)
- **Package Manager**: `uv` for development, `uvx` for end-user
  installation and execution
- **Build System**: `hatchling` or `setuptools` via `pyproject.toml`
- **Testing**: `pytest` with `pytest-asyncio` for async tool handlers
- **Linting**: `ruff` for linting and formatting
- **Type Checking**: `pyright` or `mypy` (MUST pass with no errors
  on CI)
- **Entry Point**: A `[project.scripts]` entry in `pyproject.toml`
  that starts the MCP server (e.g., `persona = "persona.server:main"`)
- **Task Runner**: GNU Make via a root-level `Makefile`

## Development Workflow

### Makefile as Project Interface

The project MUST include a `Makefile` at the repository root as the
standard interface for all common development tasks. The following
targets are mandatory:

| Target       | Command                        | Purpose                              |
|--------------|--------------------------------|--------------------------------------|
| `make run`   | Start the MCP server locally   | Launch via `uv run persona`          |
| `make test`  | Run the full test suite        | Execute `uv run pytest`              |
| `make lint`  | Run linter and formatter check | Execute `uv run ruff check . && uv run ruff format --check .` |
| `make check` | Run lint then test             | Composite: depends on `lint` + `test` |

Additional targets MAY be added (e.g., `make format`, `make typecheck`,
`make build`) but MUST NOT conflict with or shadow the four mandatory
targets above. `make check` MUST be the single command a developer
runs before committing to verify the codebase is clean.

### General Workflow

- **Branching**: Feature branches MUST use the format
  `feat-<NNN>-<descriptive-name>` where `NNN` is the zero-padded
  spec number (e.g., `feat-002-ci-pipeline`,
  `feat-003-add-weather-tool`). Branches are created using
  `git worktree add` from the main working tree to enable parallel
  feature development. Worktrees live under `../worktrees/<branch>`
  relative to the main working tree (e.g.,
  `../worktrees/feat-003-my-feature`). Each worktree gets its own
  VS Code window and Claude Code session. Spec-kit scripts do NOT
  create branches — developers create the worktree/branch first,
  then run spec-kit from within the worktree. Merge via pull request.
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`,
  `refactor:`, `test:`, `chore:`).
- **Pre-merge gates**: `make check` MUST pass. This is equivalent
  to all tests passing and linting being clean.
- **Tool addition process**: Spec the tool (name, description, input
  schema, output schema) → write failing contract test (TDD red) →
  implement handler until tests pass (TDD green) → refactor →
  verify via MCP Inspector or client.
- **Release**: Version in `pyproject.toml` follows SemVer. Publish
  to PyPI triggers on tagged releases.

## Governance

This constitution is the authoritative source of project standards.
All code reviews and planning artifacts MUST verify compliance with
these principles. Amendments require:

1. A written proposal describing the change and rationale.
2. Update to this file with version bump per SemVer rules:
   - MAJOR: Principle removal or backward-incompatible redefinition.
   - MINOR: New principle or materially expanded guidance.
   - PATCH: Wording clarifications or typo fixes.
3. Propagation check across all `.specify/templates/` files.

**Version**: 1.4.0 | **Ratified**: 2026-02-07 | **Last Amended**: 2026-02-10
