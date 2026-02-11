# Feature Specification: SQLite Storage

**Feature Branch**: `feat-003-sqlite`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "Migrate to sqlite as a db to store all resume data rather than using local markdown files. Not in production — breaking changes and data loss are fine. Prefer simple, clean design."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Store and Retrieve Resume Data (Priority: P1)

As a user, I want my resume data stored in a structured database so that reads and writes are reliable, atomic, and free from the fragility of markdown parsing.

**Why this priority**: This is the core purpose of the feature — replacing markdown file storage with a database. Everything else depends on data being stored and retrieved correctly.

**Independent Test**: Can be fully tested by writing resume data (contact, summary, experience, education, skills) via MCP tools and reading it back, verifying 100% fidelity.

**Acceptance Scenarios**:

1. **Given** a user with no existing data, **When** they add contact information, experience, education, and skills, **Then** all data is persisted and retrievable exactly as entered.
2. **Given** a user with existing resume data, **When** they retrieve their full resume, **Then** all sections are returned completely and accurately.
3. **Given** a write operation that fails validation, **When** the error occurs, **Then** no partial data is persisted.

---

### User Story 2 - Database Initializes Automatically (Priority: P1)

As a user installing the tool, I want the database to be created automatically on first use so that I can start immediately without any setup.

**Why this priority**: Zero-configuration is essential for the `uvx` distribution model. The tool must work out of the box.

**Independent Test**: Can be fully tested by starting the system with no pre-existing data directory and verifying the database is created and all tools function.

**Acceptance Scenarios**:

1. **Given** a fresh installation with no data directory, **When** the MCP server starts, **Then** the data directory and database are created automatically.
2. **Given** an existing data directory without a database, **When** the MCP server starts, **Then** the database is created within the existing directory.

---

### User Story 3 - Manage Resume Entries (Priority: P1)

As a user, I want to add, update, and remove individual entries (jobs, education, skills) so that I can keep my resume current over time.

**Why this priority**: CRUD operations on list-type sections are the primary way users interact with the tool. Without this, the tool has no write functionality.

**Independent Test**: Can be fully tested by adding entries, modifying them, removing them, and verifying the resume reflects each change.

**Acceptance Scenarios**:

1. **Given** an empty resume, **When** a user adds a work experience entry, **Then** the entry appears in the resume.
2. **Given** a resume with 3 experience entries, **When** the user updates the second entry, **Then** only that entry changes and ordering is preserved.
3. **Given** a resume with skills, **When** the user removes a skill, **Then** it is no longer present in the resume.
4. **Given** a user attempts to add a duplicate skill (same name), **When** the operation is attempted, **Then** an error is returned indicating the duplicate.

---

### User Story 4 - Schema Changes Are Applied Automatically (Priority: P2)

As a user upgrading to a new version, I want any database schema changes to be applied automatically so that I never lose data or need to manually modify my database.

**Why this priority**: As the tool evolves, the data schema will change. Without migration handling, users would need to delete their database and lose all data on every upgrade. This is the foundation for a sustainable development workflow.

**Independent Test**: Can be fully tested by creating a database at an older schema version, starting the system, and verifying that all data is preserved and the schema is updated to the current version.

**Acceptance Scenarios**:

1. **Given** a database at schema version 1, **When** the system starts with a new version requiring schema version 2, **Then** the schema is updated and all existing data is preserved.
2. **Given** a database at the current schema version, **When** the system starts, **Then** no migration runs and the system starts normally.
3. **Given** a migration that fails partway through, **When** the error occurs, **Then** the database is left unchanged (migration is rolled back) and the user sees a clear error message.
4. **Given** a database created by a future version (higher schema version than the running code), **When** the system starts, **Then** the system refuses to start and displays a message explaining the version mismatch.

---

### Edge Cases

- What happens when the database file is inaccessible (e.g., permissions)?
- What happens when disk space is exhausted during a write?
- What happens when the configured data directory is read-only?
- If a migration is interrupted (e.g., process killed mid-migration), the system detects inconsistent schema state on next startup, displays a clear error message, and requires the user to delete and recreate the database.
- If the database has been manually modified outside the tool, no special handling is performed. Standard database errors surface naturally if manual edits cause issues.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store all resume data (contact info, summary, experience, education, skills) in a structured database, replacing markdown file storage entirely.
- **FR-002**: System MUST automatically create and initialize the database schema when no database exists.
- **FR-003**: System MUST wrap write operations in transactions to ensure atomicity.
- **FR-004**: System MUST preserve the configurable data directory behavior (`PERSONA_DATA_DIR` environment variable and `~/.persona` default).
- **FR-005**: System MUST validate data before persisting (required fields, data types, duplicate detection for skills).
- **FR-006**: System MUST return clear, descriptive error messages for validation failures.
- **FR-007**: System MUST preserve ordering for experience and education entries (newest first) and group skills by category.
- **FR-008**: System MUST NOT require any manual setup — database creation is fully automatic.
- **FR-009**: System MUST track the current schema version in the database.
- **FR-010**: System MUST automatically detect and apply pending schema migrations on startup, preserving all existing data.
- **FR-011**: System MUST apply each migration within a transaction so that a failed migration leaves the database unchanged.
- **FR-012**: System MUST refuse to start if the database schema version is newer than the version the running code supports, displaying a clear version mismatch message.

### Key Entities

- **Contact**: A single record containing personal information (name, email, phone, location, LinkedIn, website, GitHub).
- **Summary**: A single text record containing the professional summary.
- **Work Experience**: An ordered collection of job entries, each with title, company, dates, location, and highlight items.
- **Education**: An ordered collection of academic entries, each with institution, degree, field, dates, and honors.
- **Skill**: A collection of named skills, each belonging to a category. Skills are unique by name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Data round-trip fidelity is 100% — every field written can be read back identically.
- **SC-002**: `make check` passes cleanly (all tests, linting, type checking).
- **SC-003**: System starts and is usable within 2 seconds on a fresh install.
- **SC-004**: Write operations that fail validation leave the database unchanged.
- **SC-005**: Upgrading from any prior schema version to the current version preserves 100% of existing data.
- **SC-006**: A failed migration leaves the database in its pre-migration state with no data loss.

## Clarifications

### Session 2026-02-11

- Q: Should the MCP tool interface be redesigned or preserved during the SQLite migration? → A: Preserve current tool signatures; change only the storage layer behind them.
- Q: What should happen when a migration is interrupted mid-process? → A: Detect inconsistent state on startup, display a clear error message, and require the user to delete and recreate the database.
- Q: What should happen when the database has been manually modified outside the tool? → A: No special handling — rely on standard database error reporting if manual edits cause issues.

## Assumptions

- This product is pre-production. Breaking changes to the MCP tool interface are acceptable. No backward compatibility with existing tool signatures is required.
- No migration from existing markdown data is needed. Existing `resume.md` files can be ignored.
- The `python-frontmatter` dependency can be removed since markdown storage is being replaced entirely.
- The existing Pydantic models will continue to be used for data validation.
- Concurrent write safety is handled by the database engine's built-in locking; no application-level locking is needed for this single-user tool.
- Future aspiration: the server will eventually run remotely with Postgres as the database. The migration framework should be designed with portability in mind (sequential numbered migrations, version tracking), but Postgres-specific concerns are out of scope for this feature.
- The current MCP tool interface (6 tools) will be preserved as-is. Only the storage layer behind the tools changes; tool signatures, names, and behavior contracts remain the same.
- Schema migrations are sequential and numbered. Each migration knows how to move the schema from version N to N+1. Migrations are not reversible (no downgrade path).

## Out of Scope

- Migration of existing markdown data to the new database.
- Redesign of the MCP tool interface (tool signatures are preserved).
- Query or search functionality beyond basic CRUD.
- Multiple resume support.
- Backup/restore commands.
- A heavyweight migration framework (e.g., Alembic). Migrations should be simple, code-driven, and proportional to this tool's scope.
