# Plan 003 - Contacts Feature

Date: 2026-05-01

New top-level Contacts resource for networking + work relationships. CRUD via REST + MCP + UI. Taggable. Mirrors Note feature shape (user-scoped, free-form notes, tags) plus networking-specific fields.


## Requirements

### R1 - Contact Data Model

Single `contact` table per user. Schema favors KISS: small set of structured fields + rich markdown `notes` field for everything else (interests, priorities, comm prefs, collab ideas).

* Required: `name`. All other fields optional.
* Structured fields: `email`, `phone`, `company`, `title`, `relationship` (free-text suggestion list: Colleague, Recruiter, Manager, Mentor, Peer, Friend, Other), `linkedin_url`, `location`, `last_contacted_date` (ISO date), `followup_date` (ISO date)
* Rich field: `notes` (markdown, ≤10000 chars) — captures comm preferences, interests, what they care about, current priorities, collab opportunities, interaction log
* `tags: list[str]` — same normalization as other resources (lowercase, trim, dedup, ≤50 chars)
* User-scoped via `user_id` FK to `users(id)` ON DELETE CASCADE
* `created_at`, `updated_at` timestamps


### R2 - REST API

Full CRUD at `/api/contacts`, mirrors `/api/notes` shape.

* `GET /api/contacts?tag=&q=` — list summaries; multi-tag AND filter; `q` substring search across name, company, title, notes
* `GET /api/contacts/tags` — user-scoped tag list (registered BEFORE `/{contact_id}`)
* `GET /api/contacts/{id}` — full detail
* `POST /api/contacts` — create (201)
* `PATCH /api/contacts/{id}` — partial update
* `DELETE /api/contacts/{id}`
* Unified `/api/tags` aggregator includes contact tags
* 422 on validation (blank name, oversized fields, bad tag)


### R3 - MCP Tools

Match note_tools pattern. Auth via `require_user_id()`.

* `list_contacts(tag, q)` → summaries
* `get_contact(id)` → full
* `create_contact(name, email?, phone?, company?, title?, relationship?, linkedin_url?, location?, last_contacted_date?, followup_date?, notes?, tags?)`
* `update_contact(id, ...same optional fields)`
* `delete_contact(id)`


### R4 - Frontend UI

New Contacts section reachable from nav + landing page card. List view + detail/edit view. Mirror `NoteListView` / `NoteDetailView` UX.

* Nav link "Contacts" + `/contacts` and `/contacts/:id` routes
* `ContactListView`: grid/list of contact cards (name, company, title, relationship badge, tags chip row), tag chip-input filter using `listAllTags()`, q search, inline create
* `ContactDetailView`: view mode renders structured fields + markdown notes (`MarkdownContent`); edit mode uses `EntryForm`-style fields + `AutoResizeTextarea` for notes + `TagInput` w/ `listAllTags()`
* LandingPage Contacts card already exists (per recent commit) — link target `/contacts`
* `relationship` rendered as colored chip; suggestion datalist for entry
* Empty states + delete confirm via `ConfirmDialog`


### R5 - Tests

* Backend unit: `_normalize_tags`, validators (blank name, oversize notes, bad date)
* Backend contract: `/api/contacts` CRUD, `?tag=` AND, `?q=` search, `/api/contacts/tags`, `/api/tags` includes contact tags
* Backend integration: MCP tools end-to-end
* Frontend component: `ContactListView` filter+search, `ContactDetailView` view/edit roundtrip
* `make check` green


## Design

**Naming:** old singleton `contact` table dropped in v2 — name reusable. Pydantic class `Contact` (collides with nothing; existing `ContactInfo` and `ApplicationContact` distinct). Table = `contact`. Service = `ContactService`. Routes mounted alongside notes/applications.

**Schema migration v7→v8:**
```sql
CREATE TABLE contact (
    id                    SERIAL PRIMARY KEY,
    user_id               TEXT NOT NULL,
    name                  TEXT NOT NULL,
    email                 TEXT,
    phone                 TEXT,
    company               TEXT,
    title                 TEXT,
    relationship          TEXT,
    linkedin_url          TEXT,
    location              TEXT,
    last_contacted_date   TEXT,
    followup_date         TEXT,
    notes                 TEXT NOT NULL DEFAULT '',
    tags                  TEXT NOT NULL DEFAULT '[]',
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_contact_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_contact_user ON contact(user_id);
CREATE INDEX idx_contact_updated ON contact(updated_at DESC);
CREATE INDEX idx_contact_followup ON contact(followup_date) WHERE followup_date IS NOT NULL;
UPDATE schema_version SET version = 8;
```

**Pydantic models:**
```python
class Contact(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    title: str | None = None
    relationship: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    last_contacted_date: str | None = None
    followup_date: str | None = None
    notes: str = ""
    tags: list[str] = []
    created_at: str = ""
    updated_at: str = ""

class ContactSummary(BaseModel):
    id: int
    name: str
    company: str | None = None
    title: str | None = None
    relationship: str | None = None
    followup_date: str | None = None
    tags: list[str] = []
    updated_at: str = ""
```

**Service:** `ContactService(conn)`. Same shape as `NoteService` — `list_contacts`, `list_tags`, `get_contact`, `create_contact`, `update_contact`, `delete_contact`. Validation: name required + ≤255, notes ≤10000, tags via shared `_normalize_tags` (50-char limit), date fields validated as ISO date or empty.

**Tag aggregation:** `/api/tags` aggregator gains `contact_service.list_tags(uid)` line. `q` search in DB layer: `WHERE name ILIKE %q% OR company ILIKE %q% OR title ILIKE %q% OR notes ILIKE %q%`.

**Frontend types:**
```ts
export interface Contact {
  id: number; name: string; email?: string; phone?: string;
  company?: string; title?: string; relationship?: string;
  linkedinUrl?: string; location?: string;
  lastContactedDate?: string; followupDate?: string;
  notes: string; tags: string[];
  createdAt: string; updatedAt: string;
}
export interface ContactSummary { /* subset */ }
```

**API client:** `listContacts`, `listContactTags`, `getContact`, `createContact`, `updateContact`, `deleteContact` in `services/api.ts`. snake↔camel mapping at boundary (existing pattern).

**UI layout:** `ContactListView` similar to `NoteListView` — top filter bar (tag chips + q search), inline create card, then list. Each card: name (heading) · relationship chip · company / title · tag row · followup date if set. `ContactDetailView` two-column on wide: left structured fields (labeled rows w/ icons from lucide-react: Mail, Phone, Building, Briefcase, MapPin, Linkedin, Calendar), right notes (MarkdownContent). Edit mode swaps to form inputs.

**Landing page:** existing Contacts card → `to="/contacts"`. Confirm card already created (commit `9e36bf3`); flag as wired in T22.


## Tasks

### P1 - DB Migration + Models

- [ ] T01 `migrations.py`: add `migrate_v7_to_v8` (CREATE TABLE + indexes), append to `MIGRATIONS`
- [ ] T02 `models.py`: add `Contact`, `ContactSummary` w/ validators (name non-blank, ISO date format on date fields)


### P2 - DB Layer

- [ ] T03 `database.py`: `_row_to_contact`, `_row_to_contact_summary`; `create_contact`, `load_contact`, `load_contacts(user_id, tags, q)`, `update_contact`, `delete_contact`, `load_contact_tags(user_id)` — mirror note functions; tags ILIKE pattern `%"{tag}"%`


### P3 - Service Layer

- [ ] T04 `contact_service.py`: `ContactService` class w/ injected `DBConnection`; reuse `_normalize_tags` helper (extract to `tags.py` shared module if not yet — else duplicate matching note pattern); validate name, notes length, date format


### P4 - API Routes

- [ ] T05 `routes.py`: accept `contact_service` param in `create_router`; register `/api/contacts` GET/POST, `/api/contacts/tags` (BEFORE `/{id}`), `/api/contacts/{id}` GET/PATCH/DELETE
- [ ] T06 `routes.py`: extend `/api/tags` to merge `contact_service.list_tags(uid)`


### P5 - MCP Tools

- [ ] T07 `tools/contact_tools.py`: `register_contact_tools(mcp, get_service)` w/ list/get/create/update/delete; `__init__.py` export
- [ ] T08 `server.py`: instantiate `_contact_service`, pass to `create_router`, call `register_contact_tools`


### P6 - Frontend Types + API Client

- [ ] T09 `types/resume.ts`: `Contact`, `ContactSummary` interfaces
- [ ] T10 `services/api.ts`: `listContacts`, `listContactTags`, `getContact`, `createContact`, `updateContact`, `deleteContact`; snake↔camel mapping


### P7 - Frontend Components

- [ ] T11 `ContactListView.tsx` + `.module.css`: filter bar (tag chips via `listAllTags()` + q search), inline create form, contact card list, link to detail
- [ ] T12 `ContactDetailView.tsx` + `.module.css`: view mode (structured fields w/ lucide icons + MarkdownContent for notes), edit mode (form + AutoResizeTextarea + TagInput), delete via ConfirmDialog
- [ ] T13 `Navigation.tsx`: add Contacts link
- [ ] T14 `App.tsx` (or router config): add `/contacts` and `/contacts/:id` routes
- [ ] T15 LandingPage Contacts card: confirm `to="/contacts"` set


### P8 - Tests

- [ ] T16 Backend unit: `contact_service` validation + tag normalization
- [ ] T17 Backend contract: `/api/contacts` CRUD, tag filter, q search, `/api/contacts/tags`, `/api/tags` aggregation
- [ ] T18 Backend integration: MCP create→list→get→update→delete roundtrip
- [ ] T19 Frontend tests: `ContactListView` (filter, search, create), `ContactDetailView` (view/edit, delete confirm)
- [ ] T20 Run `make check` from root — all green


### Implementation Notes

- T01 → T02 → T03 (schema before DB before service). P3 blocks P4/P5.
- P4 + P5 + P6 parallel after P3.
- P7 depends on P6.
- Naming care: `Contact` (new) vs existing `ContactInfo` (resume contact info) vs `ApplicationContact` (per-application contact). Do NOT conflate — keep imports explicit.
- `application_contact` table stays untouched. Future enhancement: link `application_contact` rows to `contact.id` (out of scope here).
- `relationship` field intentionally free-text not enum — datalist suggestions only. Avoids migration churn if values evolve.
- ISO date validation: regex `^\d{4}-\d{2}-\d{2}$` — keep simple, no full calendar parsing.
- Notes markdown reuses existing `MarkdownContent` component — no new lib.
- Followup index supports future "due followups" view; not built in this feature.
- Suggest extracting `_normalize_tags` to `persona/tags.py` shared module since it's now duplicated in 4+ services — small refactor at start of P3 OR follow existing duplication and defer. Recommend: defer to keep this PR scoped; open follow-up.
- ULTRAREVIEW after P7 complete; merge after P8 green.
