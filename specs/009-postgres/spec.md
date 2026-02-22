# Feature Specification: PostgreSQL Migration & Test Strategy

**Feature Branch**: `009-postgres`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "I want to move away from sqlite and use postgres instead. Running locally via make run, which in turn uses docker compose, should use a postgres container. Help me with the best approach for unit tests, I need recommendations on best practice for tests that rely on the db."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Runs Application Locally (Priority: P1)

A developer runs `make run` and the entire application starts up — backend and a PostgreSQL database — using Docker Compose, with all data persisted between restarts. No manual database setup is required; the system handles initialization automatically.

**Why this priority**: This is the baseline — without a working local run, nothing else matters. It must work out of the box for any developer who clones the repo.

**Independent Test**: Run `make run`, wait for healthy status, then hit the API to confirm data reads and writes succeed and survive a container restart.

**Acceptance Scenarios**:

1. **Given** a fresh checkout with no prior data, **When** `make run` is executed, **Then** the application starts successfully, the database schema is initialized, and the API responds to health checks within 30 seconds.
2. **Given** a running stack with data written to the database, **When** `make run` is stopped and restarted, **Then** all previously written data is still present and accessible.
3. **Given** the application is running, **When** a developer inspects the Docker Compose setup, **Then** they see a named PostgreSQL service alongside the app service, with its data stored in a named volume.

---

### User Story 2 - Developer Runs the Test Suite (Priority: P2)

A developer runs `make test` (or `cd backend && make test`) and all tests pass — including tests that exercise database operations — against real PostgreSQL behavior (not SQLite). Tests run fast, are isolated from each other, and leave no lasting state.

**Why this priority**: Tests validate correctness. If they run against a different engine than production, they may miss subtle behavioral differences (e.g., type coercion, constraint enforcement, query planner behavior). Test isolation prevents flakiness.

**Independent Test**: Run `make test` from the backend directory; confirm all existing database tests pass with zero cross-test pollution.

**Acceptance Scenarios**:

1. **Given** the test suite is run, **When** any single test that touches the database executes, **Then** it operates against a real PostgreSQL instance (not SQLite), and its changes are rolled back or cleaned up before the next test runs.
2. **Given** two tests that write conflicting data, **When** they run sequentially, **Then** neither test sees the other's data — each test starts with a clean slate.
3. **Given** the CI environment (GitHub Actions), **When** `make check` is executed, **Then** the full test suite passes without requiring a pre-installed PostgreSQL binary on the runner host.
4. **Given** a unit test for business logic that depends on the database layer, **When** the test runs, **Then** it completes without starting any external process, using a controlled test double for the database connection.

---

### User Story 3 - Developer Writes New DB-Dependent Tests (Priority: P3)

A developer adding a new feature that touches the database can follow a documented pattern for writing tests — knowing exactly when to use an isolated real database vs. a mock/stub, and how to set up each.

**Why this priority**: Without a clear convention, developers will invent inconsistent patterns. A documented strategy prevents test debt accumulation.

**Independent Test**: A developer with no prior context can read the test strategy documentation and write a correct, isolated DB test for a new feature within 15 minutes.

**Acceptance Scenarios**:

1. **Given** a new database operation is added, **When** a developer wants to test it, **Then** there is a clear fixture or helper they can use to get a fresh, isolated database connection pre-loaded with the full schema.
2. **Given** a developer wants to test business logic that calls the database, **When** the underlying behavior does not require real SQL semantics, **Then** there is a documented pattern for passing a mock or stub connection to keep the test purely in-memory and dependency-free.
3. **Given** the test helpers are in place, **When** a developer runs a subset of DB tests in isolation (e.g., `pytest tests/unit/test_database.py`), **Then** they complete successfully without requiring a manually started database.

---

### Edge Cases

- What happens when the PostgreSQL container is not yet ready when the app container starts? The app must wait and retry rather than crash immediately.
- What happens if a database migration fails mid-way on a fresh PostgreSQL instance? The failure must be surfaced clearly and the database must not be left in a partially migrated state.
- What happens when `make test` is run without Docker available? The test suite should fail with a clear, actionable error message explaining the dependency.
- What happens to existing SQLite data when migrating? Since this is a personal/local tool, existing SQLite data is not automatically migrated — the developer starts with a fresh PostgreSQL database.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `make run` command MUST start both the application and a PostgreSQL database as co-located services, with no additional manual setup required.
- **FR-002**: The PostgreSQL database data MUST be persisted in a named Docker volume, surviving container restarts.
- **FR-003**: The application MUST wait for the PostgreSQL service to be healthy before accepting traffic (startup dependency ordering).
- **FR-004**: The application MUST run all pending schema migrations automatically at startup — before accepting any traffic — against the configured PostgreSQL instance. No separate migration container or manual CLI step is required.
- **FR-005**: All existing functional behavior — resume versions, applications, contacts, communications, accomplishments, user isolation — MUST continue to work identically after the migration.
- **FR-006**: The test suite MUST run database tests against a real PostgreSQL engine, not SQLite, to validate actual production behavior.
- **FR-007**: Each test that touches the database MUST be isolated — changes made in one test MUST NOT affect any other test.
- **FR-008**: The CI pipeline MUST be able to run the full test suite without requiring a pre-installed PostgreSQL binary on the runner (e.g., by using Docker-based test infrastructure).
- **FR-009**: Unit tests for pure business logic MUST have a documented pattern for injecting a mock/stub database connection, keeping those tests dependency-free.
- **FR-010**: The database connection configuration (host, port, credentials, database name) MUST be supplied through environment variables with sensible defaults for local development.
- **FR-011**: The PostgreSQL credentials used in local development MUST NOT be hard-coded in application source files; they MUST come from environment configuration.
- **FR-012**: The application MUST manage PostgreSQL connections via a connection pool (minimum 1, maximum 10 connections), replacing the current single shared connection. Pool size MUST be configurable via environment variables.

### Key Entities

- **PostgreSQL Service**: A named Docker Compose service running PostgreSQL, with a named volume for data persistence, health checks, and environment-configurable credentials.
- **Database Migration**: A mechanism to create and evolve the PostgreSQL schema — functionally equivalent to the existing SQLite migration sequence — executed automatically by the application process at startup, before the first request is served. No external migration runner or manual step is required.
- **Test Database Fixture**: A shared pytest fixture that provides a real PostgreSQL connection (via container) with automatic per-test transaction rollback for isolation.
- **DB Mock/Stub**: A lightweight in-memory object satisfying the existing database connection abstraction, used in pure unit tests to avoid external process dependencies.
- **Connection Pool**: A managed pool of reusable PostgreSQL connections (min 1, max 10) shared across request handlers; eliminates the per-connection threading workarounds required by the prior single-connection SQLite approach.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `make run` starts all services and the application passes its health check within 30 seconds on a cold start, with no manual database setup required.
- **SC-002**: `make test` completes successfully with all existing tests passing after the migration, with zero test failures caused by engine-specific SQL differences.
- **SC-003**: Each database-touching test runs in isolation — no shared mutable state between tests — verified by running the suite in random order without failures.
- **SC-004**: The full test suite runs to completion in CI (GitHub Actions) without a pre-installed PostgreSQL binary, relying solely on Docker-based infrastructure.
- **SC-005**: A developer can write a new database test following the established pattern in under 15 minutes, measured by the clarity and discoverability of test fixtures.
- **SC-006**: Application data written before a `docker compose down` (without `--volumes`) is fully accessible after the next `docker compose up`.

## Clarifications

### Session 2026-02-20

- Q: Does the app use a single shared connection or a connection pool for PostgreSQL? → A: Connection pool (min 1 / max 10); eliminates existing threading workarounds in the SQLite implementation.
- Q: What triggers schema initialization/migration? → A: App runs migrations automatically at startup before accepting requests — same as existing SQLite behavior, no extra container or command needed.

## Assumptions

- Existing SQLite data does not need to be migrated to PostgreSQL. This is a personal/local tool and a fresh start is acceptable.
- The PostgreSQL version used will be a current stable release (16 or 17). No legacy PostgreSQL compatibility is required.
- Docker must be available for `make run` and for running integration tests; this is already a prerequisite for the current `make run` workflow.
- Local development credentials (e.g., user `persona`, password `persona`, database `persona`) are non-sensitive defaults acceptable in `.env.example` and `docker-compose.yml` — production deployments supply their own via environment variables.
- The `DBConnection` protocol interface does not need to change. Individual connections checked out from the pool satisfy it natively. The pool itself is a separate lifecycle concern managed at the application layer (not surfaced through `DBConnection`).
- Recommended PostgreSQL Python driver: `psycopg` (psycopg3), which is actively maintained and has native async support for future use.
- Recommended test infrastructure: `testcontainers-python` (Docker-based, works on CI without a local PostgreSQL install). `pytest-postgresql` (requires a local `pg_ctl` binary) is NOT recommended as it fails on CI runners without a PostgreSQL installation.
- Recommended test isolation mechanism: transaction rollback per test (begin → test → rollback), not schema recreation per test — rollback is substantially faster at scale.
- Recommended test layering: (1) pure unit tests inject a mock/stub connection for business logic with no external process; (2) database integration tests use a real PostgreSQL container scoped to the test session with per-test rollback; (3) contract/API tests continue existing patterns pointing at the PostgreSQL-backed connection.
