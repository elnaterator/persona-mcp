# Plan 005 - Generic Resource Links

Date: 2026-05-03

Single polymorphic `resource_link` table connects any two resources of types `application`, `accomplishment`, `resume`, `note`, `contact`. One service, one MCP tool pair, one REST route, one UI panel. Replaces what would have been Plan 005 (note links) + Plan 006 (contact links) — both roadmap items satisfied.


## Requirements

### R1 - Single Polymorphic Link Table

Schema v9→v10. One table covers every pair.

* `resource_link(left_type TEXT, left_id INT, right_type TEXT, right_id INT, user_id TEXT, created_at TIMESTAMP)`
* PK `(left_type, left_id, right_type, right_id)` after canonical ordering (see Design)
* CHECK `(left_type, left_id) <> (right_type, right_id)` (no self-link)
* CHECK `left_type IN ('application','accomplishment','resume','note','contact')` (same for right_type)
* `user_id NOT NULL` denormalized for fast scoping + index `idx_link_user_left ON resource_link(user_id, left_type, left_id)` and `idx_link_user_right ON resource_link(user_id, right_type, right_id)`
* No real FKs to source tables — cascade handled in service layer (delete service for each resource calls `unlink_all(type, id)` before deleting row)


### R2 - REST API

One mutation pair, embedded reads.

* `POST /api/links` body `{ a_type, a_id, b_type, b_id }` → 201 (200 if existed) — order of a/b irrelevant, server canonicalizes
* `DELETE /api/links` body same shape → 204
* `GET /api/{type}/{id}` response gains `links: { application: ResourceRef[], accomplishment: ResourceRef[], resume: ResourceRef[], note: ResourceRef[], contact: ResourceRef[] }` (only non-empty groups returned, but type stable)
* `GET /api/{type}` rows gain `link_count: int`
* `ResourceRef = { type, id, name, updated_at }` where `name` = display label per type
* 404 if either resource not owned by user; 422 on bad type or self-link


### R3 - MCP Tools

Two tools total. Reads ride existing resource tools.

* `link_resources(a_type, a_id, b_type, b_id)`
* `unlink_resources(a_type, a_id, b_type, b_id)`
* Existing `get_application` / `get_accomplishment` / `get_resume` / `get_note` / `get_contact` responses embed `links` (grouped by type)
* Existing `list_*` responses embed `link_count`
* Net MCP delta: **+2 tools** (covers both roadmap items)


### R4 - Resource Cascade

Deleting a resource removes its links cleanly.

* Each resource delete service (`delete_application`, `delete_accomplishment`, `delete_resume_version`, `delete_note`, `delete_contact`) calls `link_service.unlink_all(type, id, uid)` before/within same transaction
* `unlink_all` deletes all rows where `(left_type, left_id) = (t, id) OR (right_type, right_id) = (t, id)` AND `user_id = uid`


### R5 - Frontend - Unified Links Panel

Every resource detail page shows the same `<LinksPanel>` component.

* `LinksPanel` (`{ resourceType, resourceId, links: GroupedLinks, onChange }`) — single section "Links" near bottom of detail view
* Renders one `LinkBox` per non-empty target type; collapsed `LinkBox`es shown for empty types behind "+ Link" picker only
* Header shows total count: "Links (N)" with single `+ Link` button → opens `LinkPickerModal` with type-tabs (All / Applications / Accomplishments / Resumes / Notes / Contacts), defaults to "All" mixing types
* Each row: type badge + name + click → navigate to `/<type>s/:id` + `×` to unlink (confirm)
* Mounted on all 5 detail views: `ApplicationDetailView`, `AccomplishmentDetailView`, `ResumeView`, `NoteDetailView`, `ContactDetailView`


### R6 - Frontend - List Counts

Every resource list view shows link count badge.

* All 5 list views render `🔗 N` badge per row when `linkCount > 0`
* Existing list endpoints already extended in R2 to include `link_count`


### R7 - Tests

* Backend unit: canonical ordering (link a→b == link b→a, single PK row); self-link rejected; cross-user link rejected; idempotent insert; `unlink_all` removes both directions; bad type 422
* Backend contract: `POST/DELETE /api/links`; `links` embedded in all 5 resource detail GETs; `link_count` on all 5 list endpoints; cross-user isolation
* Backend integration: MCP `link_resources` → `get_<a>` (verify `links`) → `get_<b>` (verify reverse `links`) → `unlink_resources`; cascade on resource delete
* Frontend component: `LinksPanel` (renders grouped types, navigates, unlinks); `LinkPickerModal` (tab filter, search, picks across types); count badge on lists
* `make check` green at root


## Design

**Why polymorphic single table** — Five resource types × bidirectional = 10 directional pairings, or 10 typed join tables (5 choose 2 = 10 unordered). Per-pair tables = 10 migrations, 10 SQL templates per service method, 10 cascade hooks. Single polymorphic table = 1 schema, 1 service, 1 route, 1 component. Trade-off: lose PG-level FK integrity, gain massive surface reduction. Cascade in service layer is 5 one-line calls — manageable.

**Canonical ordering** — Insert always normalizes so `left_type < right_type` lexicographically; if same type, `left_id < right_id`. This guarantees `link(note, 5, application, 12)` and `link(application, 12, note, 5)` produce the same row. PK + UNIQUE on canonical tuple = idempotent without `ON CONFLICT` gymnastics across direction. Read helpers query by `(user_id, type, id)` against UNION of `left` and `right` indexes.

**Migration v9→v10:**
```sql
CREATE TABLE resource_link (
    left_type   TEXT NOT NULL,
    left_id     INTEGER NOT NULL,
    right_type  TEXT NOT NULL,
    right_id    INTEGER NOT NULL,
    user_id     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (left_type, left_id, right_type, right_id),
    CONSTRAINT resource_link_no_self CHECK (
        (left_type, left_id) <> (right_type, right_id)
    ),
    CONSTRAINT resource_link_left_type_valid CHECK (
        left_type IN ('application','accomplishment','resume','note','contact')
    ),
    CONSTRAINT resource_link_right_type_valid CHECK (
        right_type IN ('application','accomplishment','resume','note','contact')
    ),
    CONSTRAINT resource_link_canonical CHECK (
        left_type < right_type
        OR (left_type = right_type AND left_id < right_id)
    ),
    CONSTRAINT fk_resource_link_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_link_user_left  ON resource_link(user_id, left_type, left_id);
CREATE INDEX idx_link_user_right ON resource_link(user_id, right_type, right_id);
UPDATE schema_version SET version = 10;
```

**Resource registry** (`link_service.py`):
```python
RESOURCE_TYPES = ('application','accomplishment','resume','note','contact')
NAME_QUERIES = {
    'application':    ('application',    'title'),  # fallback to company in code
    'accomplishment': ('accomplishment', 'title'),
    'resume':         ('resume_version', 'label'),
    'note':           ('note',           'title'),
    'contact':        ('contact',        'name'),
}
OWNERSHIP_QUERIES = {  # SELECT 1 FROM <table> WHERE id = %s AND user_id = %s
    t: f"SELECT 1 FROM {tbl} WHERE id = %s AND user_id = %s"
    for t, (tbl, _) in NAME_QUERIES.items()
}
```

**Service API:**
```python
def canonicalize(a_type, a_id, b_type, b_id) -> tuple[str,int,str,int]: ...
def link(a_type, a_id, b_type, b_id, uid) -> None
def unlink(a_type, a_id, b_type, b_id, uid) -> None
def list_links(resource_type, resource_id, uid) -> dict[str, list[ResourceRef]]
def count_links(resource_type, resource_ids: list[int], uid) -> dict[int, int]  # bulk for list views
def unlink_all(resource_type, resource_id, uid) -> None  # cascade hook
```

`list_links` query (single round-trip, returns both directions):
```sql
SELECT 'left' AS side, right_type AS other_type, right_id AS other_id
FROM resource_link
WHERE user_id = %s AND left_type = %s AND left_id = %s
UNION ALL
SELECT 'right' AS side, left_type AS other_type, left_id AS other_id
FROM resource_link
WHERE user_id = %s AND right_type = %s AND right_id = %s
```
Then for each `(other_type, other_id)` group, batch-fetch names via per-table `SELECT id, <name_col> FROM <table> WHERE id = ANY(%s)`. 5 queries max.

**Pydantic models** (`models.py`):
```python
class ResourceRef(BaseModel):
    type: Literal['application','accomplishment','resume','note','contact']
    id: int
    name: str
    updated_at: datetime | None = None

GroupedLinks = dict[str, list[ResourceRef]]  # keys: RESOURCE_TYPES
```

Each existing resource detail model gains `links: GroupedLinks = {}`. Each summary gains `link_count: int = 0`.

**Resume↔application FK stays** — `application.resume_version_id` is 1:N with semantic meaning ("the resume submitted with this app"). Different from peer linking. Leave untouched. UI optionally surfaces "Submitted Resume" as a separate field (already does). `LinksPanel` does not include it. Future: could auto-populate a `resource_link` row on resume_version_id set, but creates dual-source-of-truth — defer.

**Frontend types** (`types/resume.ts`):
```ts
export type ResourceType = 'application' | 'accomplishment' | 'resume' | 'note' | 'contact'
export interface ResourceRef {
  type: ResourceType
  id: number
  name: string
  updatedAt?: string
}
export type GroupedLinks = Partial<Record<ResourceType, ResourceRef[]>>
```

Each resource detail type adds `links: GroupedLinks`; each summary adds `linkCount?: number`.

**API client** (`services/api.ts`):
* `linkResources(aType, aId, bType, bId)` → POST /api/links
* `unlinkResources(aType, aId, bType, bId)` → DELETE /api/links
* No new read calls — embedded in existing `getApplication`/`getAccomplishment`/`getResume`/`getNote`/`getContact`

**Components:**
* `LinksPanel` (`{ resourceType, resourceId, links, onChange }`) — single section, renders header w/ total count + `+ Link` button + grouped list of `LinkBox`es (one per non-empty type)
* `LinkBox` (`{ type, items, onRemove, onNavigate }`) — pure presentational; type icon + label + collapsed/expanded list; same component type-agnostic
* `LinkPickerModal` (`{ excludeRefs, onPick(ref: ResourceRef) }`) — tabs across 5 types (default "All" merges fetches), search-as-you-type filter, click row = onPick
  * "All" mode parallel-fetches all 5 list endpoints, merges, sorted by `updated_at desc`
  * Excludes already-linked refs + self
* Routing: `useNavigate()` to `/<type>s/:id` (resume → `/resumes/:id`)

**Cascade wiring** — in each resource delete service (5 places), one new line before existing delete:
```python
link_service.unlink_all(resource_type='note', resource_id=note_id, uid=uid)
```
Done within same DB transaction (existing service patterns already use single conn).

**Performance** — Personal-scale data (<10K rows total). Bulk count for list views uses single query per list:
```sql
SELECT resource_id, COUNT(*) FROM (
  SELECT left_id AS resource_id FROM resource_link
    WHERE user_id = %s AND left_type = %s AND left_id = ANY(%s)
  UNION ALL
  SELECT right_id FROM resource_link
    WHERE user_id = %s AND right_type = %s AND right_id = ANY(%s)
) t GROUP BY resource_id
```

**Roadmap coverage** — This single plan satisfies BOTH "Link notes to any other resource" AND "Link contacts to any other resource" roadmap items. Delete second item (or mark "covered by Plan 005") when done.


## Tasks

### P1 - Schema + Models

- [x] T01 `migrations.py`: `migrate_v9_to_v10` creating `resource_link` table + canonical CHECK + indexes; append to `MIGRATIONS`
- [x] T02 `models.py`: add `ResourceRef`, `GroupedLinks` alias; extend each resource detail model w/ `links: GroupedLinks`; extend each summary w/ `link_count: int = 0`


### P2 - DB + Service Layer

- [x] T03 `database.py`: helpers `link_insert(canonical_tuple, uid)`, `link_delete(canonical_tuple, uid)`, `links_for_resource(type, id, uid)`, `link_counts(type, ids, uid)`, `unlink_all_for(type, id, uid)`
- [x] T04 `link_service.py` (new): `RESOURCE_TYPES`, `NAME_QUERIES`, `canonicalize`, `link`, `unlink`, `list_links`, `count_links`, `unlink_all`; ownership validation per type
- [x] T05 Wire `unlink_all` into each delete service: `application_service.delete_application`, `accomplishment_service.delete_accomplishment`, `resume_service.delete_resume_version`, `note_service.delete_note`, `contact_service.delete_contact`
- [x] T06 Extend each resource read service to fetch + embed `links`; extend each list query to embed `link_count` via bulk `count_links`


### P3 - REST Routes

- [x] T07 `routes.py`: `POST /api/links`, `DELETE /api/links` (body validates types, server canonicalizes)
- [x] T08 `routes.py`: verify all 5 resource detail GETs return `links` and all 5 list GETs return `link_count` (model + service changes from P2 should flow through; add response model updates if needed)


### P4 - MCP Tools

- [x] T09 `tools/link_tools.py` (new): `link_resources(a_type, a_id, b_type, b_id)`, `unlink_resources(...)`; register in `server.py`
- [x] T10 Confirm existing `get_application`/`get_accomplishment`/`get_resume`/`get_note`/`get_contact` MCP tools surface `links` field (rides on Pydantic model change in T02)


### P5 - Frontend Types + API Client

- [x] T11 `types/resume.ts`: add `ResourceType`, `ResourceRef`, `GroupedLinks`; extend each resource detail type w/ `links`; extend summaries w/ `linkCount`
- [x] T12 `services/api.ts`: `linkResources`, `unlinkResources`; extend snake↔camel mapping for `links` and `link_count` on all 5 resources


### P6 - Frontend Components

- [x] T13 `LinkBox.tsx` + `.module.css` (new): pure presentational — type icon + label + count + expandable list w/ row click + `×` unlink
- [x] T14 `LinkPickerModal.tsx` + `.module.css` (new): type tabs (All + 5 specific); parallel-fetches list endpoints in "All" mode; client-side filter; excludes already-linked + self; click = onPick
- [x] T15 `LinksPanel.tsx` + `.module.css` (new): `{ resourceType, resourceId, links, onChange }`; header w/ total count + `+ Link`; renders `LinkBox` per non-empty group; calls `linkResources`/`unlinkResources` then `onChange`


### P7 - Frontend Wiring

- [x] T16 Mount `<LinksPanel resourceType=... resourceId=... links={resource.links} onChange={refetch} />` on `ApplicationDetailView`, `AccomplishmentDetailView`, `ResumeView`, `NoteDetailView`, `ContactDetailView`
- [x] T17 Render `🔗 N` badge on `ApplicationListView`, `AccomplishmentListView`, `ResumeListView`, `NoteListView`, `ContactListView` rows when `linkCount > 0`


### P8 - Tests

- [x] T18 Backend unit: canonical ordering (link a↔b idempotent regardless of arg order); self-link rejected; cross-user rejected; bad type rejected; `unlink_all` removes both directions; bulk `count_links`
- [x] T19 Backend contract: `POST/DELETE /api/links`; `links` embedded in all 5 detail GETs; `link_count` on all 5 list GETs; cross-user isolation
- [x] T20 Backend integration: MCP `link_resources(note, X, application, Y)` → `get_note` shows app in `links.application` AND `get_application` shows note in `links.note` → `unlink_resources` clears both → delete resource cascades unlinks
- [x] T21 Frontend test: `LinksPanel` (renders groups, navigates, unlinks); `LinkPickerModal` (tab switch, "All" merge, filter, picks, excludes); list count badge
- [x] T22 `make check` green at root


### Implementation Notes

- Order: T01→T02→T03→T04→T05→T06. P3/P4 parallel after P2. P5 parallel w/ P3/P4. P6 depends on P5. P7 depends on P6. P8 last.
- Roadmap: deletes need for separate Plan 006 — both bullets satisfied here. Update `roadmap.md` to mark "Link contacts to any other resource" as covered by Plan 005 once merged.
- `application.resume_version_id` FK column is intentionally NOT migrated to `resource_link`. Different cardinality (at most one) and different semantic meaning (the submitted resume). Surfaces separately in UI as "Submitted Resume" field. Document in Design.
- Canonical ordering done in service layer, not enforced by DB beyond CHECK. CHECK exists as defense-in-depth so direct SQL inserts can't bypass canonicalization.
- "All" mode in `LinkPickerModal` parallel-fetches 5 endpoints — fast at personal scale; if slow later, gate behind tab activation (lazy load per tab).
- Empty-state UX: `LinksPanel` w/ zero links shows "No links yet" + `+ Link` button, no per-type empty boxes.
- Display labels per type: name field per `NAME_QUERIES`; for `application`, use `title` if set else `company || ' - ' || position`.
- Self-link CHECK at DB layer; service also pre-validates with cleaner 422 message ("Cannot link a resource to itself").
- Resource type tab icons (lucide-react): Application=Briefcase, Accomplishment=Trophy, Resume=FileText, Note=StickyNote, Contact=User.
- ULTRAREVIEW after P7. Merge after P8 green. Update `roadmap.md` to mark both items covered.
