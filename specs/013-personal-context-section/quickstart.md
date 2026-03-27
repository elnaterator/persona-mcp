# Quickstart: Personal Context Notes (013)

**Branch**: `013-personal-context-section`
**Date**: 2026-03-26

---

## Running the Application

```bash
# From repo root — build frontend then run backend locally
make run-local

# Or use Docker Compose
make run
```

The server starts on `http://localhost:8000` by default.

---

## Verifying the Notes Feature

### Via the UI

1. Open `http://localhost:8000` in a browser.
2. Navigate to the **Notes** tab/section.
3. Create a new note:
   - Fill in the **Title** (required).
   - Optionally enter **Content** (body text).
   - Optionally add **Tags** (comma-separated; autocomplete suggests existing tags from notes and accomplishments).
   - Save.
4. Verify the new entry appears in the list, sorted by most recently modified.
5. Click the entry to open the detail view; confirm title, content, and tags are shown.
6. Edit the content and add a tag; save and confirm only the changed fields updated.
7. Test search: enter a keyword in the search box and verify matching notes are displayed.
8. Test tag filter: select a tag and verify only notes with that tag appear.
9. Delete the entry; confirm it no longer appears in the list.

### Via the REST API

```bash
# Create a note
curl -s -X POST http://localhost:8000/api/notes \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Python async patterns",
    "content": "Key learnings from async services with asyncio and FastAPI.",
    "tags": ["python", "async"]
  }' | python3 -m json.tool

# List notes
curl -s http://localhost:8000/api/notes | python3 -m json.tool

# Search by keyword
curl -s "http://localhost:8000/api/notes?q=python" | python3 -m json.tool

# Filter by tag
curl -s "http://localhost:8000/api/notes?tag=python" | python3 -m json.tool

# Combined search + tag filter
curl -s "http://localhost:8000/api/notes?q=async&tag=python" | python3 -m json.tool

# Get unique tags (for autocomplete)
curl -s http://localhost:8000/api/notes/tags | python3 -m json.tool

# Get a single note (replace 1 with actual ID)
curl -s http://localhost:8000/api/notes/1 | python3 -m json.tool

# Update (partial patch)
curl -s -X PATCH http://localhost:8000/api/notes/1 \
  -H 'Content-Type: application/json' \
  -d '{"content": "Updated async patterns notes.", "tags": ["python", "async", "fastapi"]}' | python3 -m json.tool

# Delete
curl -s -X DELETE http://localhost:8000/api/notes/1 | python3 -m json.tool
```

### Via the MCP Server

Using an MCP client (e.g., Claude Desktop or MCP Inspector at `http://localhost:8000/mcp`):

```
# List all notes
list_notes()

# Search by keyword
list_notes(q="python")

# Filter by tag
list_notes(tag="async")

# Combined search
list_notes(q="patterns", tag="python")

# Create
create_note(
  title="Python async patterns",
  content="Key learnings from async services.",
  tags=["python", "async"]
)

# Get full detail
get_note(id=1)

# Update
update_note(id=1, content="Updated learnings.", tags=["python", "async", "fastapi"])

# Delete
delete_note(id=1)
```

---

## Running Tests

```bash
# All tests (backend + frontend)
make check

# Backend only
cd backend && make check

# Frontend only
cd frontend && make check

# Specific backend test files
cd backend && uv run pytest tests/unit/test_note_service.py -v
cd backend && uv run pytest tests/contract/test_note_api.py -v
```

---

## Schema Migration

The note table is added in schema migration v5→v6. The migration runs automatically when the server starts against a v5 database. To verify:

```bash
# After running the server once, check the table exists
psql $DATABASE_URL -c "\d note"
```
