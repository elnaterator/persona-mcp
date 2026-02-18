# Research: Accomplishments Feature (007)

**Phase**: 0 — Unknowns resolved before design
**Branch**: `feat-007-accomplishments`
**Date**: 2026-02-18

---

## Decision 1: Tags Storage Strategy

**Decision**: Store tags as a JSON text array in a single `TEXT` column (`tags TEXT NOT NULL DEFAULT '[]'`).

**Rationale**: The codebase already uses JSON text storage for arrays — the `highlights` column in the old `experience` table used the identical pattern (`highlights TEXT NOT NULL DEFAULT '[]'`). A separate join table would require more complex queries and a new migration structure for no benefit at single-user scale. JSON array parsing in Python (via `json.loads`) is trivially fast.

**Alternatives considered**:
- Separate `accomplishment_tag(accomplishment_id, tag)` table: normalized but adds a JOIN to every read, complicates tag update (delete-all + re-insert), and is premature for personal-tool scale.

**Tag normalization**: Tags are trimmed of leading/trailing whitespace at the service layer before persistence.

**Autocomplete source**: The `GET /api/accomplishments/tags` endpoint derives unique tags in Python by iterating the JSON arrays across all accomplishments, deduplicating, and sorting alphabetically. No caching needed for single-user, small dataset.

---

## Decision 2: Date Field Format and Sort Order

**Decision**: `accomplishment_date` stored as `TEXT` in ISO 8601 date format (`YYYY-MM-DD`), nullable. Sort order is `ORDER BY accomplishment_date DESC NULLS LAST, created_at DESC` — accomplishments without a date fall to the bottom, those with the same date are sub-sorted by creation time.

**Rationale**: All date fields in the existing schema (`start_date`, `end_date`, `date`) use TEXT with ISO format. SQLite's TEXT comparison works correctly for ISO 8601 dates. `NULLS LAST` ensures entries without a date don't suppress recent entries. Sub-sorting by `created_at DESC` provides a deterministic order for same-day entries.

**Alternatives considered**:
- INTEGER epoch timestamps: harder to read/debug in SQLite directly, inconsistent with existing convention.
- `DATETIME` type: SQLite has no native DATETIME type; text is the idiomatic choice.

---

## Decision 3: No New Third-Party Dependencies

**Decision**: Zero new third-party dependencies are required for this feature.

**Rationale**: All required functionality is available through the existing stack:
- SQLite JSON array: `json.loads` / `json.dumps` from Python stdlib
- Partial update pattern: existing dict-based service layer handles it
- Tag autocomplete: derived at the endpoint layer from existing data
- Frontend date input: standard HTML `<input type="date">`, no date-picker library needed

Constitution Principle IV (Minimal Dependencies) is satisfied without any waivers.

---

## Decision 4: Service Class and File Structure

**Decision**: Create `AccomplishmentService` in `backend/src/persona/accomplishment_service.py`, following the exact same pattern as `ApplicationService` in `application_service.py`. Register MCP tools in `backend/src/persona/tools/accomplishment_tools.py` via `register_accomplishment_tools(mcp, get_service)`.

**Rationale**: The `ApplicationService` pattern is the established, tested pattern for this codebase. New features follow the same layered architecture: DB functions → Service class → API routes + MCP tools. `create_router` in `routes.py` gains an optional `acc_service: AccomplishmentService | None = None` parameter mirroring `app_service`.

---

## Decision 5: REST Update Method

**Decision**: Use `PATCH /api/accomplishments/{id}` (not PUT) for partial updates, consistently on both the FastAPI route and the frontend API client.

**Rationale**: FR-008 requires updating any combination of fields without overwriting others — this is semantically PATCH, not PUT (full replace). The existing codebase uses PUT in routes but PATCH in the client for applications (an inconsistency out of scope for this feature). For accomplishments, both sides will use PATCH from the start.

---

## Decision 6: Tags Endpoint Routing Order

**Decision**: Define `GET /api/accomplishments/tags` before `GET /api/accomplishments/{id}` in the route registration to prevent FastAPI from matching the literal string `"tags"` as an integer path parameter.

**Rationale**: FastAPI evaluates routes in registration order. If `/{id}` is registered first with `id: int`, the request `GET /api/accomplishments/tags` would fail with a 422 (cannot parse "tags" as int). Registering the static route first resolves the ambiguity.

---

## Summary Table

| # | Topic | Decision |
|---|-------|----------|
| 1 | Tags storage | JSON TEXT array column, service-layer trimming |
| 2 | Dates + sort order | ISO TEXT, `accomplishment_date DESC NULLS LAST, created_at DESC` |
| 3 | Dependencies | None new required |
| 4 | Service / file structure | `AccomplishmentService`, mirrors ApplicationService pattern |
| 5 | Update HTTP method | PATCH (both route and client) |
| 6 | Tags route ordering | `/tags` route registered before `/{id}` route |
