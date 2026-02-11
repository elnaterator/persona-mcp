# MCP Tool Contracts: SQLite Storage

**Feature**: feat-003-sqlite
**Date**: 2026-02-11
**Decision**: Tool signatures preserved from current implementation (per clarification).

## Overview

The MCP tool interface is **unchanged**. All 6 tools retain their current names, parameters, and return types. Only the storage layer behind them changes from markdown files to SQLite.

This document defines the behavioral contracts each tool must satisfy with the new storage backend.

---

## Tool: `get_resume`

**Signature**: `() -> dict[str, Any]`

**Contract**:
- Returns complete resume as a dictionary with keys: `contact`, `summary`, `experience`, `education`, `skills`.
- On empty database, returns default values: empty contact fields, empty string summary, empty lists for collections.
- All data returned must match exactly what was written (SC-001: 100% round-trip fidelity).

**Error behavior**: Returns empty resume structure on any read error (graceful degradation, matching current behavior).

---

## Tool: `get_resume_section`

**Signature**: `(section: str) -> dict | str | list`

**Contract**:
- `section` must be one of: `contact`, `summary`, `experience`, `education`, `skills`.
- Returns the specified section's data in the same format as the corresponding key in `get_resume()`.
- Invalid section name returns a `ValueError` with message listing valid sections.

**Return types by section**:
| Section | Return Type | Empty State |
|---------|-------------|-------------|
| `contact` | `dict` | `{"name": null, "email": null, ...}` |
| `summary` | `str` | `""` |
| `experience` | `list[dict]` | `[]` |
| `education` | `list[dict]` | `[]` |
| `skills` | `list[dict]` | `[]` |

---

## Tool: `update_section`

**Signature**: `(section: str, data: dict[str, Any]) -> str`

**Contract**:
- Valid sections: `contact`, `summary`.
- **contact**: Accepts any subset of contact fields. Merges with existing data (partial update). Missing fields in `data` are not cleared.
- **summary**: Requires `{"text": "..."}`. Replaces entire summary.
- Returns human-readable success message.
- Validates data via Pydantic before persisting (FR-005).
- On validation failure: returns error message, database unchanged (FR-003, SC-004).

**Error cases**:
| Condition | Error |
|-----------|-------|
| Invalid section | `ValueError`: section not in `[contact, summary]` |
| Empty contact data `{}` | `ValueError`: no fields to update |
| Empty summary text `""` | `ValueError`: summary text cannot be empty |
| Invalid field types | Pydantic `ValidationError` translated to descriptive message |

---

## Tool: `add_entry`

**Signature**: `(section: str, data: dict[str, Any]) -> str`

**Contract**:
- Valid sections: `experience`, `education`, `skills`.
- Creates a new entry and **prepends** it (position 0 for experience/education).
- Validates data via Pydantic model for the section.
- **Skills**: Checks for duplicate name (case-insensitive). Rejects with error if duplicate found.
- Returns human-readable success message including entry summary.
- Database unchanged on any validation error.

**Required fields by section**:
| Section | Required | Optional |
|---------|----------|----------|
| `experience` | `title`, `company` | `start_date`, `end_date`, `location`, `highlights` |
| `education` | `institution`, `degree` | `field`, `start_date`, `end_date`, `honors` |
| `skills` | `name` | `category` (defaults to "Other") |

---

## Tool: `update_entry`

**Signature**: `(section: str, index: int, data: dict[str, Any]) -> str`

**Contract**:
- Valid sections: `experience`, `education`, `skills`.
- Updates entry at 0-based `index` with partial data (merge, not replace).
- Fields not in `data` are preserved.
- Validates updated entry via Pydantic after merge.
- Returns human-readable success message.

**Error cases**:
| Condition | Error |
|-----------|-------|
| Invalid section | `ValueError` |
| `index` out of range | `ValueError` with valid range |
| Empty `data` `{}` | `ValueError`: no fields to update |
| Invalid field values | Pydantic validation error as descriptive message |

---

## Tool: `remove_entry`

**Signature**: `(section: str, index: int) -> str`

**Contract**:
- Valid sections: `experience`, `education`, `skills`.
- Removes entry at 0-based `index`.
- For experience/education: remaining entries' positions are compacted.
- Returns human-readable success message including removed entry summary.

**Error cases**:
| Condition | Error |
|-----------|-------|
| Invalid section | `ValueError` |
| `index` out of range | `ValueError` with valid range |

---

## Cross-Cutting Contracts

### Transaction Safety (FR-003, FR-011)
- All write operations (`update_section`, `add_entry`, `update_entry`, `remove_entry`) execute within a database transaction.
- On any failure, the transaction rolls back — no partial writes.

### Error Response Format (Constitution Principle V)
- All errors returned as structured MCP error responses with human-readable messages.
- No stack traces exposed to MCP clients.
- Internal exceptions caught at tool handler boundary.

### Database Initialization (FR-002, FR-008)
- If the database does not exist when any tool is called, it is created and migrated to the current schema version automatically.
- This is transparent to the tool caller.

### Schema Migration (FR-009 through FR-012)
- Migrations run on server startup, before any tool handlers are available.
- If schema version > code version: server refuses to start with version mismatch error.
- If migration fails: server refuses to start, database left unchanged.
