# Implementation Plan: CI Pipeline

**Branch**: `feature/002-ci-pipeline` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-ci-pipeline/spec.md`

## Summary

Add a GitHub Actions CI workflow that automatically runs `make check` (lint + typecheck + test) whenever a pull request is created or updated. Uses the official `astral-sh/setup-uv` action and a single `ubuntu-latest` runner with Python 3.11.

## Technical Context

**Language/Version**: Python 3.11 (minimum supported per pyproject.toml)
**Primary Dependencies**: GitHub Actions, `astral-sh/setup-uv` action
**Storage**: N/A
**Testing**: Validation by opening a PR and confirming the workflow triggers
**Target Platform**: GitHub Actions `ubuntu-latest` runner
**Project Type**: Single project — CI configuration only
**Performance Goals**: Pipeline completes within 5 minutes (SC-003)
**Constraints**: No secrets required; must work for fork PRs (public checks only)
**Scale/Scope**: Single workflow file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | N/A | CI config, not MCP functionality |
| II. Single-Package Distribution | N/A | No packaging changes |
| III. Test-Driven Development | N/A | No application code; workflow validated by PR trigger |
| IV. Minimal Dependencies | PASS | `astral-sh/setup-uv` is the only external action (official, maintained by uv authors) |
| V. Explicit Error Handling | N/A | No application code |
| Makefile targets | PASS | CI runs `make check`, the mandatory composite target |
| Branching convention | PASS | Branch is `feature/002-ci-pipeline` per convention |
| Pre-merge gates | PASS | This feature *implements* the CI pre-merge gate |

**Gate result**: PASS — no violations.

**Post-design re-check**: PASS — no changes to assessment.

## Project Structure

### Documentation (this feature)

```text
specs/002-ci-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── quickstart.md        # Phase 1: implementation guide
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── ci.yml           # GitHub Actions CI workflow (NEW)
```

**Structure Decision**: This feature adds only a CI configuration file. No changes to the existing `src/` or `tests/` structure. The `.github/workflows/` directory is the standard location for GitHub Actions workflows.

## Workflow Design

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: make check
```

**Key decisions** (see [research.md](research.md) for details):
- Single job: project is small; parallel jobs add overhead without benefit
- `pull_request` trigger: covers open + push-to-branch by default (FR-001, FR-002)
- `astral-sh/setup-uv@v4`: official action with built-in caching
- `make check`: single command matching local dev workflow (constitution)
- Python 3.11: minimum supported version per pyproject.toml

## Complexity Tracking

No constitution violations — table not applicable.
