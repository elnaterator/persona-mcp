# Plan 015 - Unified Search Experience

Date: 2026-05-25

One reusable search bar (tags + text, one box) across all list views. Generic cross-resource search API + global search on home page.


## Requirements

### R1 - SearchBar component

Single bar holds tag chips (float left) + free text. Type → tag suggestions; commit tag via Tab/Enter-on-suggestion/click → chip. Remaining typed text = search text.

* Controlled: `value: { tags: string[]; text: string }`, `onChange(next)`.
* Trailing token matches `availableTags` → dropdown; only `Tab` or click promotes token → chip. `Enter` triggers search, never promotes; blur keeps text as text (NOT auto-tag).
* `Backspace` on empty text removes last chip.
* Chips render left, removable (X); text input shares same bordered box.
* `ArrowUp`/`ArrowDown` navigate dropdown; `Escape` closes. `Enter` submits search (fires `onSubmit`), does not commit highlighted item.
* a11y: `role=listbox`/`option`, `aria-expanded`, `aria-autocomplete=list`.

### R2 - Adopt across all list views

Replace dual `TagInput` + plain `searchInput` in 5 list views with one `SearchBar`. Consistent.

* Views: resumes, applications, accomplishments, notes, contacts.
* `{tags,text}` drives existing list query `{tags, q}`.
* `text` debounced 300ms before query.
* No regression: tag filter + text filter still work per existing per-resource list endpoints.
* `TagInput` retained for tag-EDIT contexts (forms) — out of scope to replace.

### R3 - Generic cross-resource search API

`GET /api/search` fans out across all resource types, unified result shape. User-scoped.

* Query: `q` (text), `tag` (repeatable), optional `type` (filter to subset).
* Returns `SearchResult[]`: `{type, id, title, subtitle, snippet, tags, url}`.
* Covers: resume, application, accomplishment, note, contact, communication.
* Reuses existing per-service list/search; resume needs `q`+`tags` filter added.
* Per-type cap (50) + tag match semantics match existing (`ILIKE '%"tag"%'`).
* No-auth mode + Clerk-auth mode both work (uid scoping like other routes).

### R4 - Home page global search

SearchBar on home page → `/api/search` → grouped results, click navigates to item.

* Empty query → no results shown (hint text).
* Results grouped by type with counts; each row → `url` (react-router `Link`).
* Debounced; loading + empty states.
* Reuses R1 SearchBar + R3 API.


## Design

### Backend search refactor (foundation, do first)

Three simplifications underpin everything else. Land before adding new search code.

1. **`build_filters` helper** in `database.py`. Every `load_*` (`load_applications` :404, `load_accomplishments` :775, `load_notes` :951, `load_contacts`, `search_communications` :630) copy-pastes the same user_id + tags + q WHERE block. Extract:
   ```python
   def build_filters(user_id, tags, q, q_columns) -> tuple[str, list]:
       # returns (" WHERE ..." | "", params); tags use ILIKE '%"tag"%'
   ```
   Each loader passes its own `q_columns`; ~10 lines × 5 → one call each.
2. **Standardize `q` semantics → word-split AND** in the helper. Today `load_notes` splits `q` into words (AND each); the rest treat `q` as one substring — so "acme corp" matches inconsistently across types. Helper makes one behavior; pick word-split AND (better UX). Tag match semantics unchanged.
3. **Service registry** to kill the `if x is not None` × 6 fan-out repeated in `list_all_tags` (routes.py:922) and the new search. One iterable of `(type_name, service)` consumed by both `/api/tags` and `/api/search`.

### Architecture: two endpoints, two jobs (keep separate)

Per-resource list endpoints stay for list pages; `/api/search` is for the home global box only. They are NOT interchangeable:

| | per-resource `/api/notes?q=` | global `/api/search` |
|---|---|---|
| shape | full typed summary (status, followup, link_count, dates) | lossy `{title, subtitle, snippet, url}` |
| empty query | show ALL | show nothing |
| sort | resource-specific | flattened |
| cache | per-resource keys + mutation invalidation | one search key |

Routing list pages through `/api/search` would drop type-specific columns (R014 compact rows) or bloat the unified shape. Shared UI (`SearchBar`) gives consistency without API consolidation. `/api/search` is a **thin mapper over existing `list_*` methods** — N calls + field-map, zero new query logic.

### SearchBar interface

```ts
interface SearchValue { tags: string[]; text: string }
interface SearchBarProps {
  value: SearchValue
  onChange: (v: SearchValue) => void
  onSubmit?: () => void   // fired on Enter
  availableTags: string[]
  placeholder?: string
  id?: string
}
```

Diff vs `TagInput`: `TagInput` commits all typed text → tag on blur/Enter (tag-editor). `SearchBar` only promotes the trailing token to a chip on explicit Tab or click; `Enter` triggers search (`onSubmit`), text stays text. Keep both; note future consolidation if patterns converge.

### Generic search API contract

`GET /api/search?q=&tag=&tag=&type=` →

```json
[{ "type": "application", "id": 12, "title": "SWE @ Acme",
   "subtitle": "Interviewing", "snippet": "...", "tags": ["backend"],
   "url": "/applications/12" }]
```

Server fan-out via `search_service`: iterate the service registry, call each `list_*` w/ `q`+`tags`, map row → `SearchResult`, cap 50/type. No new query logic — reuses loaders (+ `build_filters`). Type→field map:

| type | title | subtitle | snippet | url |
|------|-------|----------|---------|-----|
| resume | label | "Resume" | — | /resumes/{id} |
| application | position @ company | status | — | /applications/{id} |
| accomplishment | title | — | result | /accomplishments/{id} |
| note | title | — | content (trunc) | /notes/{id} |
| contact | name | title·company | — | /contacts/{id} |
| communication | subject | parentName | body (trunc) | /contacts/{parentId} |

`SearchResult` = Pydantic model in `models.py`. Backend: `search_service.py` with `search(q, tags, types, user_id)` injecting existing services. Route registered conditionally like others.

### Frontend wiring

- `services/api/search.ts`: `globalSearch({q, tags, types})`.
- `types/search.ts`: `SearchResult`, `SearchValue`; barrel export.
- `hooks/queries/search.ts`: `useGlobalSearch({q, tags, enabled})`, key `['search', {...}]`.
- `components/SearchBar.tsx` + `.module.css` (theme tokens, reuse `TagInput` chip CSS primitives).


## Tasks

### P0 - Backend search refactor (foundation)

- [x] T01 Add `build_filters(user_id, tags, q, q_columns)` helper in `database.py`; rewrite all 5 `load_*`/`search_communications` to use it.
- [x] T02 Standardize `q` → word-split AND inside helper; update any tests asserting old substring behavior.
- [x] T03 Add service registry iterable; refactor `list_all_tags` (routes.py:922) to consume it.

### P1 - Backend generic search

- [x] T04 Add resume `q`+`tags` filter via `build_filters`: extend `resume_service.list_resumes` + `database` load fn (label + tags).
- [x] T05 Add `SearchResult` Pydantic model in `models.py`.
- [x] T06 Add `search_service.py`: iterate registry, call `list_*` w/ `q`+`tags`, map → `SearchResult`, cap 50/type, optional `types` filter.
- [x] T07 Register `GET /api/search` in `routes.py` (`q`, repeatable `tag`, optional `type`; uid scoping).

### P2 - SearchBar component

- [x] T08 Add `types/search.ts` (`SearchValue`, `SearchResult`) + barrel.
- [x] T09 Build `components/SearchBar.tsx` + `.module.css` per R1 (chips+text, dropdown, keyboard, a11y).

### P3 - Adopt in list views

- [x] T10 Replace TagInput+searchInput w/ SearchBar in resumes, applications, accomplishments, notes, contacts; debounce text 300ms; map `{tags,text}`→query `{tags,q}`.
- [x] T11 Remove now-dead `searchInput` CSS / dual-filter markup per view.

### P4 - Home global search

- [x] T12 `services/api/search.ts` + `hooks/queries/search.ts` (`useGlobalSearch`).
- [x] T13 Add SearchBar + grouped results panel to `pages/home/index.tsx`; debounce; empty/loading states; rows link via `url`.

### P5 - Tests

- [x] T14 Backend: regression test for word-split AND `q` semantics across resources (covers P0 standardization).
- [x] T15 Backend: contract test `/api/search` (text, tag, type filter, uid scoping, per-type cap).
- [x] T16 Frontend: SearchBar unit (promote via Tab/click only; Enter fires onSubmit + keeps text; backspace removes chip).
- [x] T17 Frontend: home global-search render test (grouped results, navigation url).


### Implementation Notes

- Sequence: P0 → P1 → P2 → (P3 ∥ P4) → P5. P0 is foundation (build_filters, q semantics, registry); P1 builds on it.
- Keep per-resource list endpoints for list pages — NO per-view API change. Only NEW endpoint is `/api/search` (home global box, R4). The two are not interchangeable (see Architecture design note).
- `/api/search` = thin mapper over `list_*`; no new query logic.
- Tag match keeps JSON-text semantics `ILIKE '%"tag"%'` — refactor must not regress.
- Communication already searchable (`/api/communications`); fold into registry/fan-out, drop nothing. ContactListView comm-search panel stays as-is this plan.
- Keep `TagInput` for forms (tag editing). SearchBar is filter/search only.
- Resume `q` filter (T04) is the only existing-service gap; `application/accomplishment/note/contact` already accept `q`+`tags`.
- Truncate snippet server-side (~160 chars) to keep payload small.
