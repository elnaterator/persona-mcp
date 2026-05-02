# Plan 002 - Common Tag Pool

Date: 2026-05-01

Unified tag pool across all resource types. Tags on any resource (accomplishment, note, application, resume) feed shared autocomplete. Add tags field to applications and resume versions.


## Requirements

### R1 - Unified Tag Autocomplete

Single `/api/tags` endpoint aggregates tags from all resource types. All `TagInput` components source suggestions from this endpoint — not per-resource endpoints.

* `GET /api/tags` returns sorted, deduplicated tags merged from accomplishments, notes, applications, and resume versions for current user
* All list/detail views replace multiple tag-list calls with single `listAllTags()` call
* Existing per-resource tag endpoints (`/api/accomplishments/tags`, `/api/notes/tags`) retained for backward compat
* Tag entered on a note immediately appears as suggestion when adding tag to an accomplishment (same session after reload)


### R2 - Tags on Applications

Applications gain full tag support matching accomplishment/note pattern.

* DB migration v6→v7 adds `tags TEXT NOT NULL DEFAULT '[]'` to `application` table
* `Application` and `ApplicationSummary` models include `tags: list[str] = []`
* `GET /api/applications` accepts `?tag=` query param (AND logic, multi-value)
* `GET /api/applications/tags` returns all application tags for current user
* MCP `list_applications`, `create_application`, `update_application` tools include tag params
* Tag normalization (lowercase, trim, dedup, 50-char max) applied consistently


### R3 - Tags on Resume Versions

Resume versions gain tag support for organizing variants (e.g., "backend", "leadership").

* DB migration v6→v7 adds `tags TEXT NOT NULL DEFAULT '[]'` to `resume_version` table
* `ResumeVersion` and `ResumeVersionSummary` models include `tags: list[str] = []`
* `GET /api/resume-versions/tags` returns all resume version tags for current user
* Resume version create/update API and MCP tools accept tags
* Tag normalization applied consistently


### R4 - Consistent Tag Validation

50-char limit per tag enforced uniformly. Currently only note service enforces this.

* `_normalize_tags()` in accomplishment_service, application_service, resume_service all enforce 50-char max
* Shared helper or identical validation in all service layers
* API returns 422 with clear message on tag length violation


## Design

**No new DB table.** Tags remain per-resource JSON strings. Aggregation at service/API layer only.

**Aggregated endpoint:**
```
GET /api/tags
→ merge(load_accomplishment_tags(user_id), load_note_tags(user_id),
        load_application_tags(user_id), load_resume_version_tags(user_id))
→ sorted, deduped list[str]
```

**Schema migration v6→v7:**
```sql
ALTER TABLE application ADD COLUMN tags TEXT NOT NULL DEFAULT '[]';
ALTER TABLE resume_version ADD COLUMN tags TEXT NOT NULL DEFAULT '[]';
UPDATE schema_version SET version = 7;
```

**DB tag filter pattern** (same as existing):
```sql
WHERE tags ILIKE %s  -- pattern: '%%"{tag}"%%'
```

**Frontend change:** Replace per-resource calls:
```ts
// Before (NoteListView)
const [noteTags, accTags] = await Promise.all([listNoteTags(), listAccomplishmentTags()])
const allTags = Array.from(new Set([...noteTags, ...accTags])).sort()

// After (all views)
const allTags = await listAllTags()
```

**User scoping:** `/api/tags` passes `user_id` to all underlying queries. Accomplishment tags currently global — normalize to user-scoped in this feature.

**MCP tag tools:** `list_applications` and `list_resume_versions` gain single `tag: str | None` param (matches existing pattern — not multi-tag).


## Tasks

### P1 - DB Migration + Models

Add tags columns and update Pydantic models.

- [x] T01 `migrations.py`: add `migrate_v6_to_v7` — ALTER application + resume_version, append to MIGRATIONS list
- [x] T02 `models.py`: add `tags: list[str] = []` to Application, ApplicationSummary, ResumeVersion, ResumeVersionSummary


### P2 - DB Layer

Extend database.py for tags on application and resume_version.

- [x] T03 `database.py`: `_row_to_application` — parse tags JSON; create/update application — json.dumps tags; load_applications — tags filter with ILIKE; load_application_tags — dedup sorted list
- [x] T04 `database.py`: same pattern for resume_version (load_resume_version_tags, tags in row conversion + create + update)


### P3 - Service Layer

Add tag normalization + list_tags to application and resume services. Normalize accomplishment service to also enforce 50-char limit.

- [x] T05 `application_service.py`: `_normalize_tags` (50-char limit), wire into create/update, expose `list_tags(user_id)`
- [x] T06 `resume_service.py`: same — `_normalize_tags`, `list_tags(user_id)`, tags in create/update resume version
- [x] T07 `accomplishment_service.py`: add 50-char limit to existing `_normalize_tags`


### P4 - API Routes

Add application tag endpoints, resume version tag endpoint, and unified `/api/tags`.

- [x] T08 `routes.py`: `GET /api/applications` — add `tag: list[str] | None = Query(default=None)` filter
- [x] T09 `routes.py`: `GET /api/applications/tags` — user-scoped; register BEFORE `/{app_id}`
- [x] T10 `routes.py`: resume version create/update — accept and persist tags
- [x] T11 `routes.py`: `GET /api/resume-versions/tags` — user-scoped
- [x] T12 `routes.py`: `GET /api/tags` — aggregate all four tag sources, return merged sorted list


### P5 - MCP Tools

Extend application and resume MCP tools with tag params.

- [x] T13 `application_tools.py`: add `tags: list[str] | None` to create/update, `tag: str | None` to list filter
- [x] T14 resume MCP tools: add `tags: list[str] | None` to create/update resume version


### P6 - Frontend Types + API Client

Update TypeScript types and API service functions.

- [x] T15 `types/resume.ts`: add `tags: string[]` to Application, ApplicationSummary; add to ResumeVersion, ResumeVersionSummary if they exist as interfaces
- [x] T16 `api.ts`: new `listAllTags(): Promise<string[]>` calling `GET /api/tags`; update application create/update/list to include tags; update resume version create/update to include tags


### P7 - Frontend Components

Wire tag UI into application and resume views; switch all views to unified tag list.

- [x] T17 ApplicationListView: add `tagFilter` state, multi-tag filter chip input using `listAllTags()`; show tags on list items
- [x] T18 ApplicationDetailView: display tags in view mode; TagInput in edit mode using `listAllTags()`
- [x] T19 ResumeVersionListView (or equivalent): tag display + TagInput in edit mode
- [x] T20 AccomplishmentListView, AccomplishmentDetailView, NoteListView, NoteDetailView: replace per-resource tag-list calls with `listAllTags()`


### P8 - Tests

Update and add tests to cover new tag behavior.

- [x] T21 Backend unit tests: tag normalization in application_service and resume_service (50-char limit, lowercase, dedup)
- [x] T22 Backend contract tests: `/api/applications?tag=`, `/api/applications/tags`, `/api/tags` aggregation
- [x] T23 Frontend component tests: ApplicationListView/DetailView tag rendering; unified tag autocomplete
- [x] T24 Run `make check` from root — all green before PR


### Implementation Notes

- T01 must complete before T03/T04 (schema before DB layer).
- T02 must complete before T05/T06 (models before services).
- P3 and P4 can run in parallel after P2 done.
- P5 and P6 can run in parallel with P4.
- P7 depends on P6.
- P8 runs after P7.
- Accomplishment tags currently not user-scoped at API layer (`list_accomplishment_tags` has no user_id) — T12 aggregation must handle this; consider scoping accomplishment tags to user_id for consistency (small change in routes.py + database.py).
- Do not break existing tag filter behavior on accomplishments/notes — regression risk.
- ILIKE pattern `%"{tag}"%` correctly handles exact tag match within JSON array string; do not change this pattern.
