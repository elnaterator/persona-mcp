# Quickstart: CI Pipeline

## What This Feature Does

Adds a GitHub Actions workflow that automatically runs `make check` (lint + typecheck + test) on every pull request, providing immediate pass/fail feedback to contributors.

## Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | GitHub Actions workflow definition |

## Implementation Steps

1. Create `.github/workflows/ci.yml` with:
   - Trigger: `pull_request` (covers open + push to PR branch)
   - Runner: `ubuntu-latest`
   - Steps: checkout, setup Python 3.11, setup uv, install dependencies (`uv sync`), run `make check`

2. Verify locally by reviewing the YAML syntax.

3. Push the branch, open a PR, and confirm the workflow triggers and passes.

## Key Decisions

- **Single job, not matrix**: The project is small; one runner with Python 3.11 is sufficient.
- **`astral-sh/setup-uv`**: Official action from the uv authors; handles install + caching.
- **`make check` as the sole command**: Mirrors the local dev workflow per the constitution.
