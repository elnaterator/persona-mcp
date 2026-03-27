# Research: Personal Context Notes (013)

**Phase**: 0 — Unknowns resolved before design
**Branch**: `013-personal-context-section`
**Date**: 2026-03-26

---

## Decision 1: Tags Storage Strategy

**Decision**: Store tags as a JSON text array in a single `TEXT` column (`tags TEXT NOT NULL DEFAULT '[]'`), identical to the accomplishments pattern.

**Rationale**: The codebase already uses this pattern for accomplishments (007). The `tags` column stores `'["tag1","tag2"]'` as text, parsed with `json.loads`. Tag filtering uses `ILIKE '%"tag"%'` against the JSON string. This is proven at single-user scale and avoids introducing a join table.

**Alternatives considered**:
- Separate `note_tag(note_id, tag)` join table: Normalized, enables cross-entity tag queries natively in SQL, but adds JOIN complexity and a new migration pattern for no benefit at current scale. The existing JSON-in-TEXT approach is working well.

**Tag normalization**: Tags are trimmed of whitespace and lowercased at the service layer before persistence, consistent with accomplishments (which trim but do not lowercase — notes will add lowercasing as specified in the feature spec).

---

## Decision 2: Unified Tag Pool for Autocomplete

**Decision**: The tag autocomplete endpoint for notes (`GET /api/notes/tags`) returns tags from notes only. A separate unified endpoint is not needed because the frontend can merge results from `/api/notes/tags` and `/api/accomplishments/tags` client-side.

**Rationale**: Each feature's tag listing endpoint is self-contained and scoped to its own entity. The accomplishments endpoint already exists and returns accomplishment-only tags. Adding a cross-feature endpoint would couple the two services. Instead, the frontend tag input component fetches from both endpoints and merges/deduplicates the results for autocomplete suggestions. This keeps the backend simple and decoupled while delivering the unified tag pool UX specified in FR-016.

**Alternatives considered**:
- Single `/api/tags` endpoint that queries across all entities: Cleaner from the frontend's perspective but couples note and accomplishment services at the backend, requires a new cross-cutting function in database.py, and creates an unclear ownership boundary. Rejected in favor of client-side merge.

---

## Decision 3: Sort Order

**Decision**: List view sorted by `updated_at DESC` (most recently modified first). No user-controlled sort options.

**Rationale**: The spec clarification explicitly states "reverse chronological by last-modified timestamp." Unlike accomplishments (which sort by a user-editable `accomplishment_date`), notes have no user-editable date field. Sorting by `updated_at` ensures recently edited notes surface to the top, which matches the note-taking mental model (most recently touched = most relevant).

**Sort SQL**: `ORDER BY updated_at DESC`

**Alternatives considered**:
- Sort by `created_at DESC`: Would bury frequently-updated notes below newer but stale ones. Less useful for an active note collection.
- User-editable date field: Over-engineering for simple notes. The spec explicitly chose not to add one.

---

## Decision 4: No New Third-Party Dependencies

**Decision**: Zero new third-party dependencies are required for this feature.

**Rationale**: All required functionality is available through the existing stack:
- JSON array storage: `json.loads` / `json.dumps` from Python stdlib
- Substring search: PostgreSQL `ILIKE` operator (existing pattern)
- Tag autocomplete: Derived at the endpoint layer from existing data
- Frontend tag input: `<datalist>` element for autocomplete (used by accomplishments)
- Length validation: Standard Python `len()` checks at service layer

Constitution Principle IV (Minimal Dependencies) is satisfied without any waivers.

---

## Decision 5: Service Class and File Structure

**Decision**: Create `NoteService` in `backend/src/persona/note_service.py`, following the exact same pattern as `AccomplishmentService`. Register MCP tools in `backend/src/persona/tools/note_tools.py` via `register_note_tools(mcp, get_service)`.

**Rationale**: The `AccomplishmentService` pattern is the closest analogue — a standalone entity with tags, CRUD operations, and search. `create_router` in `routes.py` gains an optional `note_service: NoteService | None = None` parameter. The service follows constructor-injected DB connection pattern.

---

## Decision 6: Search Implementation

**Decision**: Keyword search uses the `q` parameter with case-insensitive `ILIKE` substring matching against `title` and `content` columns. Multiple words in the `q` parameter are split by whitespace; each word must match (AND logic). Tag filtering uses the existing `tag` parameter with `ILIKE '%"tag"%'` against the JSON column.

**Rationale**: This mirrors the existing accomplishments pattern (`q` searches across multiple fields with ILIKE) but adds AND logic for multiple terms as specified. The applications list endpoint also uses a `q` parameter for search, establishing a codebase convention.

**Search SQL pattern**:
```sql
-- For q="python deployment"
WHERE (title ILIKE '%python%' OR content ILIKE '%python%')
  AND (title ILIKE '%deployment%' OR content ILIKE '%deployment%')
-- For tag="leadership"
  AND tags ILIKE '%"leadership"%'
```

---

## Decision 7: Content Length Validation

**Decision**: Enforce maximum lengths at the service layer: title ≤ 255 characters, content ≤ 10,000 characters, each tag ≤ 50 characters. Return `ValueError` on violation.

**Rationale**: FR-011a and FR-011b require explicit validation with descriptive errors. The service layer is the single enforcement point (Constitution V — explicit error handling). The database schema does not enforce these limits (TEXT columns are unbounded in PostgreSQL), so the service layer is the correct place.

---

## Decision 8: Tags Route Ordering

**Decision**: Register `GET /api/notes/tags` before `GET /api/notes/{note_id}` in FastAPI route registration, identical to the accomplishments pattern.

**Rationale**: FastAPI evaluates routes in registration order. If `/{note_id}` (with `note_id: int`) is registered first, a request to `/api/notes/tags` would fail with 422 (cannot parse "tags" as int). This is documented as a known pattern in the codebase (see accomplishments routes comment).

---

## Summary Table

| # | Topic | Decision |
|---|-------|----------|
| 1 | Tags storage | JSON TEXT array column, service-layer trim + lowercase |
| 2 | Unified tag pool | Client-side merge of `/api/notes/tags` + `/api/accomplishments/tags` |
| 3 | Sort order | `updated_at DESC` (most recently modified first) |
| 4 | Dependencies | None new required |
| 5 | Service / file structure | `NoteService`, mirrors AccomplishmentService pattern |
| 6 | Search implementation | `q` param with ILIKE, multi-word AND, `tag` param for tag filter |
| 7 | Content length validation | Service-layer enforcement: title ≤ 255, content ≤ 10,000, tag ≤ 50 |
| 8 | Tags route ordering | `/tags` route registered before `/{note_id}` route |
