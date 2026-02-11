# Database Layer Contract

**Feature**: feat-003-sqlite
**Date**: 2026-02-11

## Module Interface: `persona.database`

New module replacing `persona.resume_store`. Provides all database operations consumed by tool handlers.

### Initialization

```python
def init_database(data_dir: Path) -> sqlite3.Connection
```
- Creates `data_dir/persona.db` if it doesn't exist.
- Opens connection with WAL mode, foreign keys ON, busy timeout 5000ms.
- Runs pending migrations via `apply_migrations()`.
- Returns the open connection.
- Raises `SchemaVersionError` if DB version > code version.
- Raises `MigrationError` if a migration fails (DB left unchanged).

### Migration

```python
def apply_migrations(conn: sqlite3.Connection) -> None
```
- Reads `PRAGMA user_version`.
- If version == `SCHEMA_VERSION`: no-op.
- If version > `SCHEMA_VERSION`: raises `SchemaVersionError(db_version, code_version)`.
- If version < `SCHEMA_VERSION`: applies migrations `[version..SCHEMA_VERSION)` sequentially, each in a transaction.
- On migration failure: rolls back current migration, raises `MigrationError`.

### CRUD Operations

All functions take `conn: sqlite3.Connection` as first argument.

```python
# Read
def load_resume(conn) -> Resume
def load_section(conn, section: str) -> ContactInfo | str | list[WorkExperience] | list[Education] | list[Skill]

# Write - contact/summary
def save_contact(conn, data: dict[str, Any]) -> None       # partial merge
def save_summary(conn, text: str) -> None                   # full replace

# Write - list entries
def add_experience(conn, data: dict[str, Any]) -> WorkExperience
def add_education(conn, data: dict[str, Any]) -> Education
def add_skill(conn, data: dict[str, Any]) -> Skill

def update_experience(conn, index: int, data: dict[str, Any]) -> WorkExperience
def update_education(conn, index: int, data: dict[str, Any]) -> Education
def update_skill(conn, index: int, data: dict[str, Any]) -> Skill

def remove_experience(conn, index: int) -> WorkExperience   # returns removed entry
def remove_education(conn, index: int) -> Education
def remove_skill(conn, index: int) -> Skill
```

### Error Types

```python
class SchemaVersionError(Exception):
    """Database schema version is newer than code supports."""
    def __init__(self, db_version: int, code_version: int): ...

class MigrationError(Exception):
    """A schema migration failed."""
    def __init__(self, from_version: int, to_version: int, cause: Exception): ...
```

### Invariants

1. All write functions validate input via Pydantic before touching the database.
2. All write functions execute within a transaction (rollback on any error).
3. `load_resume()` returns a valid `Resume` model even on empty database.
4. Index-based operations use the `position` column ordering, not raw row IDs.
5. After `add_*` to experience/education, the new entry is at index 0 and all other positions shift +1.
6. After `remove_*` from experience/education, positions are compacted (no gaps).
