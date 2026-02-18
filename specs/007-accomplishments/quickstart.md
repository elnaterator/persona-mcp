# Quickstart: Accomplishments Feature (007)

**Branch**: `feat-007-accomplishments`
**Date**: 2026-02-18

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

## Verifying the Accomplishments Feature

### Via the UI

1. Open `http://localhost:8000` in a browser.
2. Navigate to the **Accomplishments** tab/section.
3. Create a new accomplishment:
   - Fill in the **Title** (required).
   - Enter text in any or all of the **Situation**, **Task**, **Action**, **Result** fields.
   - Optionally set an **Accomplishment Date** and add **Tags**.
   - Save.
4. Verify the new entry appears in the list, sorted most-recent first.
5. Click the entry to open the detail view; confirm all STAR fields are shown (with placeholder text for any empty fields).
6. Edit the **Result** field and save; confirm only that field changed.
7. Delete the entry; confirm it no longer appears in the list.

### Via the REST API

```bash
# Create an accomplishment
curl -s -X POST http://localhost:8000/api/accomplishments \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Led platform migration",
    "situation": "Monolith caused 4-hour deploys.",
    "task": "Migrate 3 services in 6 months.",
    "action": "Coordinated 4 teams, used feature flags.",
    "result": "Reduced deploy time by 80%.",
    "accomplishment_date": "2024-03-15",
    "tags": ["leadership", "technical"]
  }' | python3 -m json.tool

# List accomplishments
curl -s http://localhost:8000/api/accomplishments | python3 -m json.tool

# Filter by tag
curl -s "http://localhost:8000/api/accomplishments?tag=leadership" | python3 -m json.tool

# Get unique tags (for autocomplete)
curl -s http://localhost:8000/api/accomplishments/tags | python3 -m json.tool

# Get a single accomplishment (replace 1 with actual ID)
curl -s http://localhost:8000/api/accomplishments/1 | python3 -m json.tool

# Update (partial patch)
curl -s -X PATCH http://localhost:8000/api/accomplishments/1 \
  -H 'Content-Type: application/json' \
  -d '{"result": "Reduced deploy time by 80%. Saved $200k/year."}' | python3 -m json.tool

# Delete
curl -s -X DELETE http://localhost:8000/api/accomplishments/1 | python3 -m json.tool
```

### Via the MCP Server

Using an MCP client (e.g., Claude Desktop or MCP Inspector at `http://localhost:8000/mcp`):

```
# List all accomplishments
list_accomplishments()

# List filtered by tag
list_accomplishments(tag="leadership")

# Create
create_accomplishment(
  title="Led platform migration",
  situation="Monolith caused 4-hour deploys.",
  action="Coordinated 4 teams.",
  result="Reduced deploy time by 80%.",
  accomplishment_date="2024-03-15",
  tags=["leadership", "technical"]
)

# Update
update_accomplishment(id=1, result="Reduced deploy time by 80%. Saved $200k/year.")

# Delete
delete_accomplishment(id=1)
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
cd backend && uv run pytest tests/unit/test_accomplishment_service.py -v
cd backend && uv run pytest tests/contract/test_accomplishment_api.py -v
```

---

## Schema Migration

The accomplishment table is added in schema migration v2→v3. The migration runs automatically when the server starts against a v2 database. To verify:

```bash
# After running the server once, inspect the schema
sqlite3 /path/to/persona.db ".schema accomplishment"
sqlite3 /path/to/persona.db "PRAGMA user_version;"  # Should output 3
```
