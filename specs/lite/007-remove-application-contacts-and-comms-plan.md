# Plan 007 - Remove application contacts and communications

Date: 2026-05-08

Drop duplicate per-application contact + communication subsystems. Apps reuse generic links (R005) to relate to networking contacts. Networking contacts keep their own communication history (R004). No data preserved (early project, no users).


## Requirements

### R1 - Backend removal

Strip application-scoped contacts + communications from DB, models, services, MCP tools, and REST API.

* New migration `v10_to_v11` drops table `application_contact` (CASCADE)
* Same migration drops cols `app_id`, `contact_id`, `contact_name` from `communication`; drops indexes `idx_application_contact_app`, `idx_communication_app`, `idx_communication_date`
* `models.py` removes `ApplicationContact`; `Communication` + `CommunicationSearchResult` lose `app_id`, `contact_id`, `contact_name`
* `database.py` removes app-contact + app-communication CRUD; `search_communications` becomes contact-only (drop `parent` arg, drop `app` join), `delete_communication_owned` drops app branch, `create_communication` removed (only `create_contact_communication` remains)
* `application_service.py` drops `add_contact`, `list_contacts`, `update_contact`, `remove_contact`, `add_communication`, `list_communications`, `update_communication`, `remove_communication`; `get_application_context` returns app + linked resources only (no `contacts` / `communications` keys)
* `tools/application_tools.py` drops 6 MCP tools: `add_application_contact`, `update_application_contact`, `remove_application_contact`, `add_communication`, `update_communication`, `remove_communication`
* `api/routes.py` drops 8 endpoints under `/api/applications/{app_id}/contacts*` + `/api/applications/{app_id}/communications*`
* All app-contact / app-comm tests deleted; remaining contact-comm + cross-iface tests pass

### R2 - Frontend removal

Remove app-scoped contacts + communications UI; rely on `LinksPanel` for related contacts/notes/etc.

* Delete `frontend/src/components/ContactsPanel.tsx` + `.module.css` (app-only)
* `CommunicationsPanel` becomes contact-only: drop `parentType` prop, accept `contactId` only; rename file if needed
* `ApplicationDetailView.tsx` removes `<ContactsPanel>` + `<CommunicationsPanel>` blocks; `LinksPanel` remains as sole relations UI
* `services/api/applications.ts` drops contact + communication methods; `types/application.ts` drops `ApplicationContact`, `Communication` (app variant)
* `types/index.ts` re-exports updated; no broken imports
* Vitest + ESLint + tsc clean

### R3 - MCP search + docs

Cross-resource comm search becomes contact-scoped; tool surface trimmed.

* `search_communications` MCP tool: drop `parent` param (or accept only `"contact"`); description updated
* `prompts.md` (specs/lite) — purge any app-contact / app-comm prompts
* `AGENTS.md` — no edits expected (no app-contact section); verify
* No README / spec doc references to deleted endpoints remain (`grep` clean)


## Design

**Schema migration (v11):**
```sql
DROP TABLE IF EXISTS application_contact CASCADE;
ALTER TABLE communication DROP COLUMN IF EXISTS app_id;
ALTER TABLE communication DROP COLUMN IF EXISTS contact_id;
ALTER TABLE communication DROP COLUMN IF EXISTS contact_name;
DROP INDEX IF EXISTS idx_application_contact_app;
DROP INDEX IF EXISTS idx_communication_app;
```
`communication` post-migration: `id, contact_ref_id (NOT NULL), type, direction, subject, body, date, status, tags, created_at`. Make `contact_ref_id` NOT NULL after column drop.

**Search simplification:** `search_communications(q, tags, user_id)` joins only `contact ct ON c.contact_ref_id = ct.id`; `parent_type` always `"contact"`.

**App context shape:**
```json
{ "application": {...}, "linked": { "contact": [...], "note": [...], "accomplishment": [...], "resume_version": [...] } }
```
Pulled from existing links system (R005).

**Frontend:** `ApplicationDetailView.panels` collapses to single `<LinksPanel>`. Users add a contact linkage instead of typing inline contact rows. Communication history lives only on `ContactDetailView`.

**Risk:** none beyond breaking cached frontend bundles; no real users.


## Tasks

### P1 - Backend schema + DB

- [x] T01 Add `migrate_v10_to_v11` in `migrations.py`; append to `MIGRATIONS`; bump `SCHEMA_VERSION`
- [x] T02 Strip `application_contact` + app-comm helpers from `database.py` (create/load/update/delete contact, `create_communication`, `load_communications`, `update_communication` app-branch); update `search_communications`, `delete_communication_owned`
- [x] T03 Update `models.py`: remove `ApplicationContact`; trim `Communication`, `CommunicationSearchResult` (drop `app_id`, `contact_id`, `contact_name`)

### P2 - Backend service + transport

- [x] T04 Strip 8 methods from `application_service.py`; simplify `get_application_context` to use links registry
- [x] T05 Remove 6 MCP tools from `tools/application_tools.py`; update `search_communications` MCP tool (drop `parent` param)
- [x] T06 Remove 8 routes from `api/routes.py` (`/applications/{id}/contacts*`, `/applications/{id}/communications*`)
- [x] T07 Delete obsolete tests: `test_application_service.py` contact/comm cases, `test_rest_api.py` matching routes, `test_cross_interface.py` app-comm cases; update `test_contact_comm_mcp.py` if `parent` param tested

### P3 - Frontend

- [x] T08 Delete `components/ContactsPanel.tsx` + `.module.css`
- [x] T09 Refactor `CommunicationsPanel` to contact-only (drop `parentType`/`parentId`, accept `contactId`); update `ContactDetailView` callsite
- [x] T10 Edit `pages/applications/ApplicationDetailView.tsx`: remove `ContactsPanel` + `CommunicationsPanel` imports + JSX; keep `LinksPanel`
- [x] T11 Trim `services/api/applications.ts` + `types/application.ts` + `types/index.ts`
- [x] T12 Run `make check` (frontend + backend); fix any fallout

### P4 - Docs + verify

- [x] T13 Sweep `specs/lite/prompts.md` + spec docs; remove app-contact / app-comm references
- [x] T14 Manual smoke: create app, link contact via `LinksPanel`, add comm on contact, verify cross-link visible from app detail (deferred — automated tests cover backend + frontend; UI smoke pending)


### Implementation Notes

- P1 → P2 → P3 strict order (DB shape drives service shape drives UI)
- T07 in parallel with T04–T06 once contracts known
- T08 + T11 parallel
- Keep `Communication` model single class — just drop nullable app fields; no split needed
- Migration is destructive; assume single-tenant dev DB (per roadmap "no users yet")
- After T02, double-check `_row_to_communication` doesn't reference dropped cols
- Don't add backwards-compat shims; no `parent="application"` fallback in search
- LinksPanel already wired (R005); no new link-type registration needed for contact↔application
