# Plan 014 - Compact List Rendering

Date: 2026-05-23

Make accomplishment, note, application, contact list items compact single-row (resume list as reference): title left, tags middle, meta (dates, counts, badges) float right, wrap to 2 lines only when needed. Fit more items per screen.


## Requirements

### R1 - Compact single-row list items

All 4 non-resume lists match resume's horizontal layout. Title cluster left (flex grow, ellipsis), tags middle (wrap), meta right (nowrap).

* Each list item primary content fits 1 line on desktop where content allows; max 2 lines when title + badges + tags overflow.
* Dates, link counts, status/relationship badges align right (float-right via flex push).
* Title truncates with ellipsis (`min-width:0` + `text-overflow:ellipsis`), never wraps mid-word to force 3rd line.
* Item vertical padding reduced from `--space-6` to compact (`--space-4`), matching denser feel; resume list also tightened to stay consistent.
* `<640px`: items collapse to vertical stack (keep existing resume mobile behavior).
* No content removed — all fields currently shown stay visible (status, relationship, sub-line, followup, dates, link count, tags).

### R2 - Shared list-row CSS primitives

Kill duplicated list/item/meta/tag CSS across 5 view modules (currently ~identical blocks). One source of truth for compact tuning.

* New shared module `frontend/src/components/listRow.module.css` holds: `list`, `item`, `itemLink`, `itemMain`, `title`, `itemMeta`, `metaItem`, `linkCount`, `tagList`, `tagBadge`.
* All 5 list view modules consume shared classes via CSS Modules `composes:` (single class name in JSX, no double-class churn).
* Per-view-only styles stay in per-view module (status colors, relationship badge, contact sub-line, app job-posting link, filters, comm search).
* Visual result identical across lists for shared parts; tuning compactness = edit 1 file.


## Design

### Reference pattern (resume, unchanged target)

```
.item        flex row, align-items:center, gap, padding compact
  .itemLink  flex:1, flex row, gap, min-width:0
    .itemMain  flex:1, min-width:0   → title + inline badge, ellipsis
    .tagList   wrap                  → tag chips (middle)
    .itemMeta  nowrap                → dates, linkCount (right)
@<640px: .item column, .itemMeta column
```

Title pushed left, meta pushed right by `itemMain flex:1`. Tags sit between, wrap to next line under content when wide.

### CSS Modules composition

Shared module exports plain classes. Per-view module:

```css
.item { composes: item from '../../components/listRow.module.css'; }
```

JSX keeps `className={styles.item}`. Per-view module adds extra props to same selector if needed (e.g. app `.itemMain` no override; contact adds sub-line class separately).

### Per-list mapping (current stacked → compact)

* **Accomplishments / Notes**: `itemTitle`(block) + `itemMeta`(block) + `itemTags`(block) → `itemMain`(title) | `tagList` | `itemMeta`(date, linkCount). Drop block margins.
* **Applications**: `itemHeader`(title col + status badge) + `itemMeta`(date,count,tags) + external job link → `itemMain`(position bold + company muted inline + status badge) | `tagList` | `itemMeta`(updated date, linkCount). Job-posting `<a>` stays sibling of `itemLink` inside `item`, pushed right (cannot nest anchor in Link). Status badge stays in main cluster (right of company) so it reads with title.
* **Contacts**: `itemHeader`(name + relationship badge) + `itemSub`(title·company) + `itemMeta`(followup,date,count) + `itemTags` → `itemMain`(name + relationship badge + sub `title·company` as secondary inline span) | `tagList` | `itemMeta`(followup, updated date, linkCount). Keep exact "Follow up: <date>" text (test asserts).

### Risk / contracts

* Tests = content/role/text based (no class/DOM-structure asserts). Verified: `ApplicationListView`, `ContactListView`, `Accomplishment/Note/ResumeListView` tests query by text/role. Keep all visible text + `data-testid="resume-list-view"` / `"application-list-view"`. Low break risk.
* No API, schema, type, MCP changes. Pure frontend CSS + JSX restructure.


## Tasks

### P1 - Shared list-row CSS

Extract compact primitives, single source.

- [x] T01 Create `frontend/src/components/listRow.module.css` with compact `list/item/itemLink/itemMain/title/itemMeta/metaItem/linkCount/tagList/tagBadge` (port resume values, padding `--space-4` vertical, keep `<640px` stack).
- [x] T02 Refactor `ResumeListView.module.css` to `composes:` shared classes; verify resume list visually unchanged (it is the reference).

### P2 - Convert 4 lists to compact

Each: rewrite JSX to itemMain|tagList|itemMeta + module composes shared.

- [x] T03 Accomplishments: JSX + `AccomplishmentListView.module.css` compose shared, single-row.
- [x] T04 Notes: JSX + `NoteListView.module.css` compose shared, single-row.
- [x] T05 Applications: JSX (position+company+status in itemMain, job-posting link pushed right) + `ApplicationListView.module.css` keep status colors, compose shared.
- [x] T06 Contacts: JSX (name+relationship+sub inline in itemMain) + `ContactListView.module.css` keep relationship badge + comm-search styles, compose shared. Preserve "Follow up: <date>" text.

### P3 - Verify

- [x] T07 `cd frontend && make check` (lint + typecheck + vitest) green.
- [x] T08 `make run` dev server; eyeball all 5 lists desktop + narrow (<640px): 1-line where fits, 2 max, meta right-aligned, ellipsis on long titles, no overflow. Check populated (tags/badges/counts) + empty states.


### Implementation Notes

* Sequence: P1 first (shared CSS + resume proof) → P2 lists trivial after → P3 verify. T03–T06 parallel-safe (independent files).
* `composes:` cross-module path is relative from the per-view module: `from '../../components/listRow.module.css'`.
* Don't add `<ListRow>` React component — JSX differs per type (status badge, sub-line, job link); CSS sharing covers reuse without forced abstraction. Revisit component extraction only if a 6th near-identical list appears.
* Resume list padding currently `--space-6 --space-7`; lowering vertical to `--space-4` increases density — confirm still comfortable, bump to `--space-5` if cramped.
* Keep tag chips in middle slot; if a heavily-tagged item pushes meta, tags wrap below (2-line case) — acceptable per roadmap ("2 if not").
