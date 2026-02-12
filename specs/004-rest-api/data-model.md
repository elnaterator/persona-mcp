# Data Model: REST API & Remote MCP Server

**Date**: 2026-02-12
**Feature**: feat-004-rest-api

## Existing Entities (Unchanged)

The SQLite schema and Pydantic models are already defined and require no changes for this feature. The REST API and MCP facades both operate on these existing entities.

### Resume (Aggregate)

| Field      | Type                | Description                        |
|------------|---------------------|------------------------------------|
| contact    | ContactInfo         | Singleton personal details         |
| summary    | str                 | Singleton summary text             |
| experience | list[WorkExperience]| Ordered list (position 0 = newest) |
| education  | list[Education]     | Ordered list (position 0 = newest) |
| skills     | list[Skill]         | Ordered list (by insertion id)     |

### ContactInfo (Singleton)

| Field    | Type       | Required | Notes            |
|----------|------------|----------|------------------|
| name     | str | None | No       |                  |
| email    | str | None | No       |                  |
| phone    | str | None | No       |                  |
| location | str | None | No       |                  |
| linkedin | str | None | No       |                  |
| website  | str | None | No       |                  |
| github   | str | None | No       |                  |

### WorkExperience (List Entry)

| Field      | Type       | Required | Notes                       |
|------------|------------|----------|-----------------------------|
| title      | str        | Yes      |                             |
| company    | str        | Yes      |                             |
| start_date | str | None | No       |                             |
| end_date   | str | None | No       |                             |
| location   | str | None | No       |                             |
| highlights | list[str]  | No       | Defaults to []              |

### Education (List Entry)

| Field      | Type       | Required | Notes                       |
|------------|------------|----------|-----------------------------|
| institution| str        | Yes      |                             |
| degree     | str        | Yes      |                             |
| field      | str | None | No       |                             |
| start_date | str | None | No       |                             |
| end_date   | str | None | No       |                             |
| honors     | str | None | No       |                             |

### Skill (List Entry)

| Field    | Type       | Required | Notes                            |
|----------|------------|----------|----------------------------------|
| name     | str        | Yes      | Case-insensitive uniqueness      |
| category | str | None | No       | Defaults to "Other" if empty     |

## New Entities

### DBConnection (typing.Protocol — not persisted)

Abstract database connection type based on PEP 249 DB-API 2.0, defined in `src/backend/db.py`. Enables future swap from SQLite to PostgreSQL.

| Method     | Signature                                    | Notes                     |
|------------|----------------------------------------------|---------------------------|
| execute    | `(sql: str, parameters: Any = ...) -> Any`   | Execute a SQL statement   |
| cursor     | `() -> Any`                                  | Create a cursor object    |
| commit     | `() -> None`                                 | Commit current transaction|
| rollback   | `() -> None`                                 | Rollback current transaction |
| close      | `() -> None`                                 | Close the connection      |

### ResumeService (class — not persisted)

Service class in `src/backend/resume_service.py` that encapsulates all resume CRUD operations. Takes a `DBConnection` in its constructor.

| Method         | Signature                                             | Returns              |
|----------------|-------------------------------------------------------|----------------------|
| `__init__`     | `(conn: DBConnection) -> None`                        | —                    |
| get_resume     | `() -> Resume`                                        | Full resume          |
| get_section    | `(section: str) -> dict`                              | Section data         |
| update_section | `(section: str, data: dict) -> str`                   | Success message      |
| add_entry      | `(section: str, data: dict) -> str`                   | Success message      |
| update_entry   | `(section: str, index: int, data: dict) -> str`       | Success message      |
| remove_entry   | `(section: str, index: int) -> str`                   | Success message      |

### HealthResponse (API-only, not persisted)

| Field  | Type | Description                                |
|--------|------|--------------------------------------------|
| status | str  | "ok" when healthy                          |

### ErrorResponse (API-only, not persisted)

| Field   | Type | Description                               |
|---------|------|-------------------------------------------|
| detail  | str  | Human-readable error message              |

## Section Classification

Used by both REST API and MCP facades to determine valid operations:

- **Singleton sections** (update via PUT): `contact`, `summary`
- **List sections** (add/update/remove entries): `experience`, `education`, `skills`
- **All valid sections**: union of singleton + list sections

## State Transitions

No new state machines. Resume sections are simple CRUD — create, read, update, delete. No draft/published workflow or approval flow.
