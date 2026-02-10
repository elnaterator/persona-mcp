# Tasks: CI Pipeline

**Input**: Design documents from `/specs/002-ci-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: Not requested in feature specification. No test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the directory structure for GitHub Actions workflows

- [x] T001 Create `.github/workflows/` directory structure

---

## Phase 2: User Story 1 - Automated Quality Checks on Pull Requests (Priority: P1) 🎯 MVP

**Goal**: CI pipeline automatically runs `make check` when a PR is created or updated, reporting pass/fail status

**Independent Test**: Open a PR with valid code and verify the pipeline runs and passes. Open a PR with a linting violation and verify it fails.

### Implementation for User Story 1

- [x] T002 [US1] Create GitHub Actions workflow file at `.github/workflows/ci.yml` with: `pull_request` trigger, `ubuntu-latest` runner, `actions/checkout@v4`, `actions/setup-python@v5` with Python 3.11, `astral-sh/setup-uv@v4`, `uv sync` for dependency install, and `make check` as the quality gate
**Checkpoint**: At this point, User Story 1 is complete. Notify user that the code is ready for manual verification.

---

## Phase 3: User Story 2 - Viewing Check Results (Priority: P2)

No additional implementation tasks required. User Story 2 is satisfied by the GitHub Actions workflow created in US1 — GitHub natively surfaces workflow results (status checks, logs) on the PR checks tab.

---

## Phase 4: Commit & Wrap-Up

**Purpose**: Commit all changes and notify user

- [x] T003 Commit all changes (workflow file, spec artifacts, constitution update) with a conventional commit message

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup (T001)
- **User Story 2 (Phase 3)**: No additional tasks — satisfied by US1 implementation
- **Commit (Phase 4)**: Depends on US1 completion (T002)

### Execution Order

- T001 → T002 → T003 (strictly sequential)

---

## Implementation Strategy

### Execution

1. T001: Create directory structure
2. T002: Create workflow file
3. T003: Commit all changes
4. User manually verifies by pushing branch and opening a PR

---

## Notes

- This is a minimal feature: 1 new file (`.github/workflows/ci.yml`)
- No application code changes required
- US2 requires no additional implementation — GitHub natively shows workflow results
- User will manually verify by pushing branch and opening a PR
