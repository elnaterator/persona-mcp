# Research: Persona MCP Server with Resume Tools

**Date**: 2026-02-09
**Feature**: 001-resume-mcp-server

## Decision 1: MCP SDK and Server Framework

**Decision**: Use the official `mcp` Python SDK (v1.26.0) with its built-in `FastMCP` high-level API.

**Rationale**: FastMCP is bundled inside the `mcp` package (`mcp.server.fastmcp.FastMCP`). It provides decorator-based tool registration, automatic JSON schema generation from Python type hints, Pydantic input validation, and handles both sync and async tool functions. It is the recommended approach in the official MCP documentation.

**Alternatives considered**:
- Low-level `MCPServer` class: More verbose, requires manual schema wiring. No benefit for this project's scope.
- `fastmcp` standalone package: Was merged into the official `mcp` SDK. Using the bundled version avoids an extra dependency.

## Decision 2: Transport

**Decision**: STDIO transport exclusively.

**Rationale**: The server is designed for local, single-user operation with AI assistants (e.g., Claude Desktop). STDIO is the standard transport for local MCP servers and requires no network configuration. The spec explicitly scopes out multi-user or remote access.

**Alternatives considered**:
- HTTP/SSE transport: Would add complexity (port management, CORS) with no benefit for the single-user local use case.

## Decision 3: Markdown + YAML Front-matter Parsing

**Decision**: Use `python-frontmatter` (v1.1.0, MIT license) for parsing and writing `resume.md`.

**Rationale**: The spec requires a Markdown file with YAML front-matter for contact info. `python-frontmatter` handles this exact format with zero dependencies, supports load/dump round-tripping, and is well-maintained. The alternative — manual YAML/Markdown splitting — is error-prone and reinvents the wheel.

**Alternatives considered**:
- Manual parsing with `PyYAML` + string splitting: Fragile, must handle edge cases (e.g., `---` delimiters in body content). `python-frontmatter` already solves this.
- `PyYAML` alone: Cannot handle the combined Markdown+YAML format without custom parsing code.

## Decision 4: Project Structure

**Decision**: Single-package src-layout with tool modules organized by domain.

**Rationale**: The constitution mandates `pyproject.toml` with a `[project.scripts]` entry point and `uvx` distribution. A src-layout (`src/persona/`) prevents import confusion between the installed package and the source tree. Tools are grouped by domain (e.g., `tools/resume.py`) to support the spec's future expansion into sibling feature directories under `jobs/`.

**Alternatives considered**:
- Flat layout (no `src/`): Can cause import shadowing during development. The src-layout is the Python packaging best practice.
- Monolithic single-file server: Would work initially but violates the extensibility goal stated in the spec.

## Decision 5: Resume Data Model

**Decision**: Use Pydantic models for in-memory representation of resume data, with `python-frontmatter` for file I/O.

**Rationale**: Pydantic is already a transitive dependency of the `mcp` SDK, so it adds no new dependency weight. It provides validation, serialization, and clear type definitions for resume entities (ContactInfo, WorkExperience, Education, Skill). The flow is: file → `python-frontmatter` → dict → Pydantic model → tool response.

**Alternatives considered**:
- Plain dicts: No validation, no IDE support, harder to maintain as the model grows.
- `dataclasses`: Lighter but lacks built-in validation. Since Pydantic is already present, there's no reason to use a less capable alternative.

## Decision 6: Tool Design

**Decision**: Expose a small set of generic, section-based MCP tools (6 total) rather than per-entity tools.

**Tools for P1 (Read — 2 tools)**:
- `get_resume` — Returns the full resume as structured data
- `get_resume_section` — Returns a specific section by name (contact, summary, experience, education, skills)

**Tools for P2 (Write — 4 tools)**:
- `update_section` — Updates a non-list section (contact or summary)
- `add_entry` — Adds an entry to a list-based section (experience, education, skills)
- `update_entry` — Updates an entry in a list-based section by index
- `remove_entry` — Removes an entry from a list-based section by index

Each write tool accepts a `section` parameter and a `data` dict. Validation is dispatched internally to per-section Pydantic models, so type safety is preserved despite the generic interface.

**Rationale**: A small tool surface (6 tools) is easier for the AI to reason about than 12+ per-entity tools. Adding a new resume section (e.g., certifications, projects) requires only a new Pydantic model and section registration — zero new tools. This aligns with the spec's stated goal of future expansion.

**Alternatives considered**:
- Per-entity tools (e.g., `add_experience`, `add_education`, `remove_skill`): 12 tools for the initial set, growing by 3 for each new section. Provides perfectly typed per-tool schemas but creates tool list clutter and significant code duplication.
- Single `read_resume` / `write_resume` tool pair: Too coarse; the AI would need to manage the full document on every edit, risking data loss.

## Decision 7: Error Handling Pattern

**Decision**: Use `ToolError` exceptions at the tool handler boundary, with structured error messages.

**Rationale**: The constitution (Principle V) requires structured error responses without exposing stack traces. FastMCP's `ToolError` maps directly to MCP error responses. Internal exceptions are caught at the handler boundary and translated.

**Alternatives considered**:
- Returning `CallToolResult(isError=True)`: More verbose, same outcome. `ToolError` is the idiomatic FastMCP pattern.

## Decision 8: Logging

**Decision**: Python `logging` module to stderr, INFO level by default, configurable via `LOG_LEVEL` environment variable.

**Rationale**: Directly specified in the spec (FR-008) and clarification session. STDIO transport requires that stdout is reserved for MCP protocol messages, so logging must go to stderr.

## Decision 9: Package Naming

**Decision**: Package name `persona` (import: `persona`, command: `persona`, PyPI: `persona`).

**Rationale**: The user specified "persona" as the tool name. The entry point will be `persona = "persona:main"` in `pyproject.toml`.
