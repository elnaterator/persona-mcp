# Plan 013 - Remove application→resume FK, use generic links

Date: 2026-05-23

`application.resume_version_id` FK duplicates the generic `resource_link` edge `application↔resume`. Drop column + model fields + tool params + resume-picker UI; resume↔app relations now flow only through `LinksPanel`. Migration backfills existing FK values into `resource_link` before drop. Resume list "X applications" badge re-sourced from typed link count (no FK JOIN).

## Requirements

### R1 - Migration backfills then drops FK

Schema v11→v12 migration moves every existing `resume_version_id` into a canonical `resource_link` row, then drops the column. No data loss.

* New `migrate_v11_to_v12` appended to `MIGRATIONS`; `SCHEMA_VERSION` becomes 12 automatically (len-derived).
* Backfill: for each `application` with non-null `resume_version_id`, insert canonical link `(left_type='application', left_id=app.id, right_type='resume', right_id=resume_version_id, user_id=app.user_id)` via `ON CONFLICT DO NOTHING` (idempotent, re-run safe).
* Canonical order verified: `'application' < 'resume'` lexicographically → application is `left`. Matches existing `resource_link_canonical` CHECK.
* `ALTER TABLE application DROP COLUMN resume_version_id` after backfill (drops implicit FK constraint with it).
* `_detect_actual_version` gains a v12 marker: `resource_link` exists AND `application` has no `resume_version_id` column → 12.
* Migration runs inside the existing try/rollback wrapper; partial failure rolls back cleanly.

### R2 - Backend model + query cleanup

Drop the FK column everywhere backend code reads/writes it; keep `ResumeVersionSummary.app_count` but re-source it.

* `models.py`: remove `resume_version_id` from `Application` and `ApplicationSummary`. Keep `ResumeVersionSummary.app_count` (now = count of linked applications).
* `database.py` `load_resume_versions`: drop `LEFT JOIN application` + `COUNT(a.id)`; no longer emits `app_count` from SQL.
* `database.py` `create_application`: remove `resume_version_id` from INSERT column list + values.
* `database.py` `load_applications`: remove `resume_version_id` from SELECT list.
* `database.py` `update_application`: remove `resume_version_id` from `updatable` tuple.
* New helper `link_counts_by_type(conn, resource_type, resource_ids, other_type, user_id)` — bulk `{id: count}` filtered to one linked type (mirrors `link_counts` but with an `other_type` predicate on both UNION arms).
* `resume_service.list_resumes`: set `r["app_count"]` from `link_counts_by_type("resume", ids, "application", uid)` (defaulting 0).

### R3 - MCP tool param removal

`application_tools.py` create/update no longer accept `resume_version_id`.

* Remove `resume_version_id` param + docstring line + dict entry from `create_application`.
* Remove `resume_version_id` param + docstring line + `("resume_version_id", …)` row from `update_application`.
* Resume association now done via existing link tools (`link`/`unlink`) — confirm those already cover `application↔resume`; no new tool needed.

### R4 - Frontend type + schema cleanup

TS types and the panel schema drop `resume_version_id`.

* `types/application.ts`: remove `resume_version_id` from `Application` and `ApplicationSummary`.
* `ApplicationPanel.tsx`: delete the `panelSchema = applicationCreateSchema.extend({ resume_version_id })` wrapper — use `applicationCreateSchema` directly (or keep the alias without the resume field).
* Confirm `schemas/application.ts` base schema has no `resume_version_id` (it's only in the panel extend today).

### R5 - Remove resume-picker UI

`ApplicationPanel` no longer renders a resume `<select>`; resume links surface through `LinksPanel` like every other linked type.

* Delete the `Resume` `SectionCard` block (view + edit) from `ApplicationPanel.tsx`.
* Remove `ResumeOption` interface, `resumeVersions` prop, `linkedResume` lookup, and `resume_version_id` default value.
* `ApplicationDetailView.tsx`: drop `useResumeList`, `resumeVersions`, the `resumeVersions=` props, and `resume_version_id` in `handleSave`.
* `ApplicationListView.tsx`: drop `useResumeList`, `resumeVersions`, the `resumeVersions=` prop, and `resume_version_id` in create handler.
* `LinksPanel` already renders application links (incl. resumes) — no panel change needed; verify resume entries appear after migration.

### R6 - Resume list badge re-sourced

Resume list-card "X applications" badge reads the link-derived `app_count`; behavior unchanged for the user.

* `ResumeListView.tsx` line ~82 keeps `{resume.app_count} application{…}` — value now comes from typed link count (R2).
* `types/resume.ts` keeps `app_count` on both resume types.
* Manual check: linking an application to a resume bumps the badge; unlinking drops it.

### R7 - Tests updated, suite green

All backend + frontend tests reflecting the removed column pass.

* `backend/tests/unit/test_database.py`: rewrite/remove `test_resume_version_id_fk` and the create-with-`resume_version_id` cases; convert `app_count` tests to assert link-derived counts (link an app → resume, expect `app_count == 1`).
* `backend/tests/unit/test_resume_service.py`: keep `"app_count" in v` assertion; add a case asserting it counts linked applications.
* Frontend `ApplicationListView.test.tsx`, `ResumeListView.test.tsx`, `routing.test.tsx`: strip `resume_version_id` from fixtures; keep `app_count` fixtures for resume cards.
* Add a migration test (contract/integration) seeding a pre-v12 row with `resume_version_id` and asserting a canonical `resource_link` exists post-migrate and the column is gone.
* `make check` green (backend pytest + frontend lint/vitest).

## Design

### Why this is safe

`resource_link` (v10) already models `application↔resume` as a first-class polymorphic edge with canonical ordering, ownership, and dedup. The FK was the only remaining bespoke edge. Generic links allow many resumes per application (no "primary" semantics) — accepted per roadmap; a `primary_resume_link_id` flag is deferred until UX demands it.

### Migration sketch

```python
def migrate_v11_to_v12(conn) -> None:
    """Backfill application.resume_version_id into resource_link, then drop it."""
    conn.execute(
        "INSERT INTO resource_link "
        "(left_type, left_id, right_type, right_id, user_id) "
        "SELECT 'application', id, 'resume', resume_version_id, user_id "
        "FROM application WHERE resume_version_id IS NOT NULL "
        "ON CONFLICT (left_type, left_id, right_type, right_id) DO NOTHING"
    )
    conn.execute("ALTER TABLE application DROP COLUMN resume_version_id")
    conn.execute("UPDATE schema_version SET version = %s", (12,))
    conn.commit()
```

Canonical guard holds: `'application' < 'resume'`, so `left_type < right_type` satisfies `resource_link_canonical`. `resume_version_id` is FK-guaranteed to reference a live `resume_version`, and `application.user_id` is the owner — ownership invariant preserved.

### Typed link count

```python
def link_counts_by_type(conn, resource_type, resource_ids, other_type, user_id):
    """{resource_id: count} of links to a specific other_type, bulk."""
    if not resource_ids:
        return {}
    rows = conn.execute(
        "SELECT resource_id, COUNT(*) AS cnt FROM ("
        "  SELECT left_id AS resource_id FROM resource_link "
        "  WHERE user_id=%s AND left_type=%s AND left_id=ANY(%s) AND right_type=%s "
        "  UNION ALL "
        "  SELECT right_id AS resource_id FROM resource_link "
        "  WHERE user_id=%s AND right_type=%s AND right_id=ANY(%s) AND left_type=%s"
        ") t GROUP BY resource_id",
        (user_id, resource_type, resource_ids, other_type,
         user_id, resource_type, resource_ids, other_type),
    ).fetchall()
    return {r["resource_id"]: r["cnt"] for r in rows}
```

`app_count` for resumes = `link_counts_by_type("resume", ids, "application", uid)`. Generic total `link_count` stays as-is from `count_links`.

### Touch map

```
backend/src/persona/
  migrations.py          + migrate_v11_to_v12, _detect_actual_version v12 marker
  database.py            load_resume_versions (drop JOIN), create_application,
                         load_applications, update_application, + link_counts_by_type
  resume_service.py      list_resumes → app_count from typed link count
  models.py              drop Application/ApplicationSummary.resume_version_id
  tools/application_tools.py  drop resume_version_id param (create + update)
frontend/src/
  types/application.ts   drop resume_version_id (both types)
  pages/applications/ApplicationPanel.tsx        drop resume picker + prop + schema extend
  pages/applications/ApplicationDetailView.tsx   drop useResumeList + prop + save field
  pages/applications/ApplicationListView.tsx     drop useResumeList + prop + create field
  pages/resumes/ResumeListView.tsx               badge unchanged (app_count re-sourced)
backend/tests/unit/{test_database,test_resume_service}.py   update
frontend/src/__tests__/{ApplicationListView,ResumeListView,routing}   update fixtures
```

### Out of scope

* "Primary resume per application" semantics — none preserved; revisit only if UX needs it.
* `link_count` total semantics — unchanged.
* Removing `useResumeList` hook itself — still used elsewhere; keep.

## Tasks

### P1 - Migration

Backfill FK into links, drop column, teach version detection.

- [x] T01 Add `migrate_v11_to_v12` (backfill INSERT…SELECT + DROP COLUMN + bump version); append to `MIGRATIONS`.
- [x] T02 Add v12 marker to `_detect_actual_version` (`resource_link` present AND no `application.resume_version_id` → 12).
- [x] T03 Migration test: seed v11-style app with `resume_version_id`, run migrate, assert canonical `resource_link` row exists and column dropped.

### P2 - Backend data layer

Remove FK from queries/models, add typed count.

- [x] T04 `database.py`: drop JOIN/COUNT in `load_resume_versions`; remove `resume_version_id` from `create_application`, `load_applications`, `update_application`.
- [x] T05 `database.py`: add `link_counts_by_type` helper.
- [x] T06 `resume_service.list_resumes`: populate `app_count` via `link_counts_by_type("resume", ids, "application", uid)`.
- [x] T07 `models.py`: remove `resume_version_id` from `Application` + `ApplicationSummary` (keep `ResumeVersionSummary.app_count`).

### P3 - MCP tools

- [x] T08 `application_tools.py`: remove `resume_version_id` param/docstring/dict-entry from `create_application` + `update_application`. Confirm `link`/`unlink` cover `application↔resume`.

### P4 - Frontend

Drop types, schema extend, resume-picker UI; verify links surface resumes.

- [x] T09 `types/application.ts`: remove `resume_version_id` from both types.
- [x] T10 `ApplicationPanel.tsx`: drop `panelSchema` extend, `ResumeOption`, `resumeVersions` prop, `linkedResume`, `resume_version_id` default, and the Resume `SectionCard`.
- [x] T11 `ApplicationDetailView.tsx` + `ApplicationListView.tsx`: remove `useResumeList`, `resumeVersions` prop, `resume_version_id` in save/create handlers.
- [x] T12 Verify `ResumeListView` badge still renders from `app_count`; `types/resume.ts` unchanged.

### P5 - Tests + verification

- [x] T13 Backend: fix `test_database.py` (drop/rewrite FK tests, convert `app_count` to link-based) + `test_resume_service.py` (assert linked-app count).
- [x] T14 Frontend: strip `resume_version_id` from `ApplicationListView.test.tsx`, `ResumeListView.test.tsx`, `routing.test.tsx` fixtures.
- [x] T15 Run `make check` (root) — backend pytest + frontend lint/vitest green. Manual: link app→resume, badge increments; resume entry shows in app `LinksPanel`.

### Implementation Notes

* Sequence: P1 → P2 → P3 backend-first (migration + data layer must land before tools). P4 frontend after backend contract drops the field, else TS types diverge from API. P5 closes.
* Migration is one-way (drop column). Backfill is idempotent (`ON CONFLICT DO NOTHING`), so re-running `apply_migrations` is safe; but the column drop is not reversible — no rollback migration provided (matches existing project convention: forward-only).
* `app_count` keeps its name + badge text to minimize churn; only its source changes (FK JOIN → typed link count). Reviewers should not see a UX diff on the resume list.
* `link_counts_by_type` is a near-clone of `link_counts` + a type predicate. Keep both; do not refactor `link_counts` callers.
* Watch the canonical ordering in the backfill: application is always `left` (`'application' < 'resume'`). Do not swap.
* Parallel opportunity: T09–T12 (frontend) can proceed once T04/T07 land; T13 (backend tests) parallel with T14 (frontend tests).
