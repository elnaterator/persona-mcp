# Research: CI Pipeline

## R1: GitHub Actions Workflow for Python + uv

**Decision**: Use a single GitHub Actions workflow with `ubuntu-latest` runner, `astral-sh/setup-uv` action for uv installation, and `make check` as the sole CI command.

**Rationale**: `astral-sh/setup-uv` is the official uv setup action maintained by Astral (the uv authors). It handles installation and caching of uv and its dependency cache out of the box. Using `make check` as the single CI command mirrors the local developer workflow exactly (constitution: "make check MUST be the single command a developer runs before committing").

**Alternatives considered**:
- Manual uv installation via `curl` — fragile, no caching, more maintenance.
- `pip install` workflow — doesn't match the project's uv-based toolchain.
- Multiple separate jobs for lint/typecheck/test — adds complexity; `make check` already composes these sequentially, and the project is small enough that a single job is faster than the overhead of spinning up multiple runners.

## R2: Workflow Trigger Events

**Decision**: Trigger on `pull_request` events with types `opened` and `synchronize` (the default for `pull_request`).

**Rationale**: The `pull_request` event fires on PR open and on pushes to the PR branch by default. This satisfies FR-001 (trigger on PR open) and FR-002 (trigger on new commits). No additional configuration needed.

**Alternatives considered**:
- `push` event — would run on every push to every branch, not just PRs. Wasteful.
- `pull_request_target` — runs in the context of the base branch; not appropriate here since we want to test the PR's code.

## R3: Python Version Strategy

**Decision**: Use Python 3.11, matching `requires-python = ">=3.11"` and `target-version = "py311"` in pyproject.toml.

**Rationale**: The project targets Python 3.11+ per the constitution and pyproject.toml. Testing on the minimum supported version catches compatibility issues early.

**Alternatives considered**:
- Matrix of 3.11, 3.12, 3.13 — overkill for this project's scope; can be added later if needed.
- Latest Python only — might miss compatibility issues with the minimum supported version.
