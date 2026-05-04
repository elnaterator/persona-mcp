# Plan 004 - Contact Communications

Date: 2026-05-02

Extend `communication` table to attach to either an application OR a networking `contact`. Add tags + cross-resource search. Reuse existing `CommunicationsPanel` on contact detail page. New search box on contacts page hits all communications (tag + text).


## Requirements

### R1 - Generalize Communication Model

`communication` row attaches to exactly one parent: application OR contact.

* Schema v8→v9: `app_id` becomes nullable; add `contact_ref_id INTEGER REFERENCES contact(id) ON DELETE CASCADE`
* CHECK: `(app_id IS NOT NULL AND contact_ref_id IS NULL) OR (app_id IS NULL AND contact_ref_id IS NOT NULL)`
* Add `tags TEXT NOT NULL DEFAULT '[]'` (JSON array, same shape as other resources)
* Index `idx_communication_contact_ref ON communication(contact_ref_id)`
* Existing app-attached rows untouched (`app_id` stays set, `contact_ref_id` NULL)
* Pydantic `Communication`: `app_id: int | None`, add `contact_ref_id: int | None`, `tags: list[str] = []`


### R2 - Contact Communication CRUD (REST)

Mirror application comm routes under `/api/contacts/{cid}/communications`.

* `GET /api/contacts/{cid}/communications` — list, date desc
* `POST /api/contacts/{cid}/communications` — create
* `PATCH /api/contacts/{cid}/communications/{cmid}` — partial update
* `DELETE /api/contacts/{cid}/communications/{cmid}`
* User-scoped: 404 if contact not owned by user; comm ownership inferred via parent
* 422 on bad type/direction/status/date/tag


### R3 - Cross-Resource Communication Search

One endpoint returns matching comms across both parents.

* `GET /api/communications?q=&tag=&parent=` — substring on subject/body/contact_name; `tag` multi AND; `parent=application|contact|all` (default `all`)
* Response items include parent label + id + name (for navigation): `{ id, parent_type, parent_id, parent_name, type, direction, subject, body, date, status, tags, contact_name }`
* User-scoped via parent ownership (JOIN application + contact, filter user_id)
* Sort date desc, limit 200


### R4 - MCP Tools

Add contact-comm tools + cross-search to `contact_tools.py` (or new `communication_tools.py`).

* `add_contact_communication(contact_id, type, direction, body, date, subject?, status?, tags?)`
* `update_contact_communication(comm_id, ...)` 
* `remove_contact_communication(comm_id)`
* `list_contact_communications(contact_id)`
* `search_communications(q?, tag?, parent?)` — returns same shape as REST


### R5 - Frontend UI

Reuse `CommunicationsPanel` on contact detail page; new search UI on contact list page.

* Refactor `CommunicationsPanel` props: `parentType: 'application' | 'contact'`, `parentId: number`. Internal API calls switch on `parentType`. App-side callsite stays working.
* Add `TagInput` (autocomplete via `listAllTags()`) to comm add/edit form
* Render tag chips on comm row
* `ContactDetailView`: append `<CommunicationsPanel parentType="contact" parentId={id} />` below structured fields/notes
* `ContactListView`: add "Search Communications" collapsible section at top — q input + tag chip filter + parent type toggle (`All | Applications | Contacts`); results render compact list, click jumps to parent detail page (anchor scroll to comm panel)
* Empty/loading/error states reuse existing patterns


### R6 - Tests

* Backend unit: nullable `app_id` + check constraint behavior; tag normalization on comms; search query builder
* Backend contract: full CRUD on `/api/contacts/{cid}/communications`; `/api/communications` search with q, tag AND, parent filter; cross-user isolation
* Backend integration: MCP add→list→update→delete on contact; search hits both parent types
* Frontend component: `CommunicationsPanel` with `parentType="contact"` (CRUD + tags); `ContactListView` search panel (debounced q, tag filter, navigates)
* `make check` green at root


## Design

**Why generalize the existing table** — communications are conceptually identical regardless of parent (type/direction/subject/body/date/status). Two parallel tables would duplicate schema, models, panel, routes, and tools. Single table with nullable parent FKs + CHECK preserves invariants and unlocks unified search trivially.

**Migration v8→v9:**
```sql
ALTER TABLE communication ALTER COLUMN app_id DROP NOT NULL;
ALTER TABLE communication ADD COLUMN contact_ref_id INTEGER
    REFERENCES contact(id) ON DELETE CASCADE;
ALTER TABLE communication ADD COLUMN tags TEXT NOT NULL DEFAULT '[]';
ALTER TABLE communication ADD CONSTRAINT communication_parent_xor CHECK (
    (app_id IS NOT NULL AND contact_ref_id IS NULL)
 OR (app_id IS NULL AND contact_ref_id IS NOT NULL)
);
CREATE INDEX idx_communication_contact_ref ON communication(contact_ref_id);
UPDATE schema_version SET version = 9;
```

**Naming clash** — existing `contact_id` column on `communication` references `application_contact(id)` (per-app contact). Do NOT reuse for new networking contact link. New column = `contact_ref_id`.

**Search query** (postgres):
```sql
SELECT c.*, a.title AS app_name, ct.name AS ct_name
FROM communication c
LEFT JOIN application a ON c.app_id = a.id
LEFT JOIN contact ct ON c.contact_ref_id = ct.id
WHERE (a.user_id = %s OR ct.user_id = %s)
  AND (%s IS NULL OR c.subject ILIKE %s OR c.body ILIKE %s
       OR c.contact_name ILIKE %s OR ct.name ILIKE %s)
  AND (%s IS NULL OR c.tags ILIKE %s)  -- per tag, ANDed in code
ORDER BY c.date DESC, c.id DESC LIMIT 200
```
For multi-tag AND, build `WHERE c.tags ILIKE %"tag"%` repeated per tag (matches existing `note`/`contact` pattern).

**Service layer** — new `CommunicationService` (extracted) owns:
* `list_for_contact(cid, uid)`, `add_for_contact(cid, data, uid)`, `update(cmid, data, uid)`, `remove(cmid, uid)`
* `list_for_application(...)` (delegate from `ApplicationService` to keep its API stable, OR keep app-side methods inline and only add contact-side here — pick **option B** to minimize churn)
* `search(q, tags, parent, uid)`

Recommendation: keep `ApplicationService` comm methods as-is, add new `ContactCommunicationService` (single-purpose) + a `search_communications` free function in `database.py`. Avoids cross-service refactor.

**Frontend types:**
```ts
export interface Communication {
  id: number
  appId?: number | null
  contactRefId?: number | null
  contactName?: string
  type: string
  direction: string
  subject: string
  body: string
  date: string
  status: string
  tags: string[]
  createdAt: string
}
export interface CommunicationSearchResult extends Communication {
  parentType: 'application' | 'contact'
  parentId: number
  parentName: string
}
```

**API client additions:**
* `listContactCommunications(cid)`, `addContactCommunication(cid, data)`, `updateContactCommunication(cid, cmid, data)`, `removeContactCommunication(cid, cmid)`
* `searchCommunications({ q?, tags?, parent? })`

**Panel refactor** — `CommunicationsPanel` currently takes `appId`. Change signature to `{ parentType, parentId }`. All API calls route via small internal switch. Update existing app callsite (`ApplicationDetailView`) to pass `parentType="application"`.

**Search UI on contacts page** — collapsible card above contact list. Inputs: text (debounce 300ms), `TagInput` chips, segmented `All|Applications|Contacts`. Empty query = panel shows hint, no fetch. Results = compact rows: date · type · direction · parent label badge · subject (truncate). Row click: route to `/applications/:id` or `/contacts/:id` and scroll to `#communications` anchor.

**Tag aggregation** — `/api/tags` already merges across resources. Extend to include comm tags via new `load_communication_tags(uid)` (UNION across both parents).


## Tasks

### P1 - Schema + Models

- [x] T01 `migrations.py`: add `migrate_v8_to_v9` (ALTER nullable app_id, ADD contact_ref_id + tags + CHECK + index), append to `MIGRATIONS`
- [x] T02 `models.py`: update `Communication` — `app_id: int | None`, add `contact_ref_id: int | None`, `tags: list[str] = []`; add `CommunicationSearchResult` w/ `parent_type`, `parent_id`, `parent_name`


### P2 - DB Layer

- [x] T03 `database.py`: relax `create_communication` to accept either parent; add helpers `create_contact_communication`, `load_contact_communications(contact_id)`, `delete_communication_owned(cmid, uid)` (JOIN ownership check), `search_communications(q, tags, parent, uid)`, `load_communication_tags(uid)`
- [x] T04 `database.py`: extend existing `update_communication` to accept `tags` field (normalize via shared helper)


### P3 - Service Layer

- [x] T05 `communication_service.py` (new): `ContactCommunicationService(conn)` — list_for_contact, add_for_contact, update, remove (validates type/direction/status/date/tags, ownership via contact load)
- [x] T06 `communication_service.py`: add `search(q, tags, parent, uid)` free function or static method; reuse `_normalize_tags` (extract to shared `tags.py` if not already — else duplicate)


### P4 - REST Routes

- [x] T07 `routes.py`: register `/api/contacts/{cid}/communications` GET/POST and `/{cmid}` PATCH/DELETE; use `require_user_id`
- [x] T08 `routes.py`: register `/api/communications` GET (search); parses `q`, multi `tag`, `parent`
- [x] T09 `routes.py`: extend `/api/tags` aggregator to include `load_communication_tags(uid)`


### P5 - MCP Tools

- [x] T10 `tools/contact_tools.py`: add `add_contact_communication`, `update_contact_communication`, `remove_contact_communication`, `list_contact_communications`
- [x] T11 `tools/contact_tools.py` (or new `communication_tools.py`): add `search_communications`; wire registration in `server.py`


### P6 - Frontend Types + API Client

- [x] T12 `types/resume.ts`: extend `Communication` (add `contactRefId`, `tags`, make `appId` optional); add `CommunicationSearchResult`
- [x] T13 `services/api.ts`: add `listContactCommunications`, `addContactCommunication`, `updateContactCommunication`, `removeContactCommunication`, `searchCommunications`; snake↔camel mapping for new fields


### P7 - Frontend Components

- [x] T14 `CommunicationsPanel.tsx`: change props to `{ parentType, parentId }`; route API calls via switch; add `TagInput` to form fields; render tag chip row on each comm
- [x] T15 `ApplicationDetailView.tsx`: update `<CommunicationsPanel appId={...} />` → `parentType="application" parentId={...}`
- [x] T16 `ContactDetailView.tsx`: append `<CommunicationsPanel parentType="contact" parentId={contact.id} id="communications" />` after notes
- [x] T17 `ContactListView.tsx`: add `CommunicationSearchPanel` above contact list — q (debounced) + TagInput + parent toggle; results list w/ click→navigate (use `useNavigate`, set hash `#communications`)
- [x] T18 `CommunicationsPanel.module.css`: tag chip styles + (panel anchor scroll-margin-top)


### P8 - Tests

- [x] T19 Backend unit: CHECK constraint blocks both-null/both-set; tag normalization; date validator; search query AND of tags
- [x] T20 Backend contract: contact-comm CRUD; `/api/communications` (q, tag AND, parent filter, cross-user isolation); `/api/tags` includes comm tags
- [x] T21 Backend integration: MCP add→list→update→delete on contact comm; search hits across parents
- [x] T22 Frontend test: `CommunicationsPanel` w/ `parentType="contact"` (CRUD + tag chips); search panel debounced query + tag filter + nav target
- [x] T23 Run `make check` from root — all green


### Implementation Notes

- T01 → T02 → T03/T04 → T05/T06. P4/P5/P6 parallel after P3. P7 depends on P6. P8 last.
- DB column name: `contact_ref_id` (NOT `contact_id` — that one already references `application_contact(id)`). Audit code in T03/T04 to avoid mixing.
- `_normalize_tags` now duplicated in 5+ places. Defer extraction to keep PR scoped (per Plan 003 follow-up).
- Search endpoint deliberately flat (not paginated) w/ 200-row cap — UI is interactive filter; if users complain, add cursor pagination later.
- Anchor scroll: `<div id="communications" style={{scrollMarginTop: 'var(--header-h, 64px)'}}>` inside `CommunicationsPanel`.
- Existing app comm tests must still pass — refactor of `CommunicationsPanel` props is a breaking signature; update `ApplicationDetailView` in same commit (T15) to keep CI green.
- `parentType` toggle UX: segmented control (3 buttons), default `All`. Persist in URL search params for shareable filters.
- ULTRAREVIEW after P7. Merge after P8 green.
