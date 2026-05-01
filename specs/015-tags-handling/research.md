# Research: Improved Tags Handling

**Feature**: 015-tags-handling  
**Date**: 2026-04-23

---

## Decision 1: Tag Input UX Pattern (Chip/Combobox)

**Decision**: Build a custom `TagInput` React component using a controlled chip list + text input + dropdown overlay. No third-party library.

**Rationale**:
- The project has a strict minimal-dependencies constitution. No tagging library (e.g., `react-select`, `downshift`) is justified when the feature scope is well-bounded.
- The existing `AutoResizeTextarea` pattern demonstrates the project's preference for thin, focused components.
- A custom component gives full CSS control aligned with the existing CSS Modules + design token system (`var(--accent-green)`, `var(--bg-input)`, etc.).

**Alternatives considered**:
- `react-select` — capable but heavyweight (~30KB gzip), opinionated styling that conflicts with existing CSS Modules approach.
- `downshift` — headless but adds a dependency for something achievable with ~100 lines of React.
- Native `<datalist>` — already used and shown to be inadequate (no chip UI, no multi-word control, no "Create new" option).

---

## Decision 2: Commit Triggers (Enter and Comma, not Space)

**Decision**: Enter and comma (`,`) commit the current typed text as a chip. Space is a regular character to allow multi-word tags.

**Rationale**: Per clarification session. Multi-word tags (e.g., "soft skills", "team leadership") already exist in the codebase and should remain supported.

**Alternatives considered**:
- Space commit — fast for single-word tags but breaks multi-word tags. Rejected.
- Space + modifier key — too complex and non-standard.

---

## Decision 3: Tag Normalization (Always Lowercase)

**Decision**: Tags are normalized to lowercase on commit in the frontend before being saved. Backend also enforces lowercase in `_normalize_tags`.

**Rationale**: Per clarification session. Prevents accidental duplicates ("Leadership" vs "leadership"). Consistent with NoteService's existing `_normalize_tags` which already lowercases.

**Gap found**: `AccomplishmentService._normalize_tags` does NOT lowercase — it only trims and deduplicates. This is an inconsistency that must be fixed as part of this feature.

**Alternatives considered**:
- Case-sensitive tags — rejected (user-confirmed).
- Preserve original casing of first occurrence — rejected (user said always lowercase).

---

## Decision 4: Multi-Tag AND Filter — Server-Side

**Decision**: Backend list endpoints accept multiple `tag` query parameters (repeated `?tag=a&tag=b`) and apply AND logic in the DB query. No client-side filtering.

**Rationale**: Per clarification session. Server-side is cleaner and avoids fetching all records when a filtered subset is needed. PostgreSQL ILIKE on JSON array already works; extending to multiple conditions is minimal.

**Implementation note**: FastAPI supports repeated query params via `tag: list[str] | None = Query(default=None)`. The `load_accomplishments` / `load_notes` DB functions extend their `WHERE` clause with one `tags ILIKE %s` condition per tag (all joined with `AND`).

**Alternatives considered**:
- Client-side filtering — fetch all, filter in browser. Simpler but wasteful for users with large datasets.
- New `?tags=a,b,c` comma-joined param — non-standard; repeated params are more idiomatic REST.

---

## Decision 5: Shared Component Strategy

**Decision**: One `TagInput` component serves both the "add tags" use case (forms) and the "filter by tags" use case (list views), controlled by an `allowCreate` prop.

- `allowCreate={true}` (default) — shows "Create new tag: [text]" option in dropdown. Used in create/edit forms.
- `allowCreate={false}` — only existing tags shown. Used in list-view filters.

**Rationale**: Same core interaction (chip list + text input + dropdown). Sharing the component ensures consistent behavior and appearance as required by SC-006.

---

## Decision 6: Dropdown Positioning

**Decision**: Dropdown is absolutely positioned below the input, `z-index` above surrounding content. Uses `useRef` + `onBlur` (delayed by `setTimeout(0)`) to close on outside click without interfering with dropdown item `onClick`.

**Rationale**: Standard pattern for combobox-style dropdowns in React without a portal. The delayed blur trick (`setTimeout(0)`) is widely used and well-understood. No need for a portal given the existing layout.

---

## Decision 7: Blur Behavior

**Decision**: On blur (focus lost), commit any non-empty typed text as a chip before closing the dropdown.

**Rationale**: Per spec assumption. Prevents accidental data loss when the user has typed a tag and clicks elsewhere. Consistent with how most tag inputs behave.

---

## Codebase Gaps Identified

1. **`AccomplishmentService._normalize_tags`** must be updated to lowercase (matching NoteService behavior). The existing unit test `test_tags_trimmed_and_persisted` will need updating to assert lowercase output.

2. **`load_accomplishments` / `load_notes`** in `database.py` accept `tag: str | None` — must change signature to `tags: list[str] | None` and build dynamic AND conditions.

3. **`AccomplishmentService.list_accomplishments` / `NoteService.list_notes`** — signature change from `tag: str | None` to `tags: list[str] | None`.

4. **FastAPI routes** (`GET /api/accomplishments`, `GET /api/notes`) — change `tag: str | None` to `tag: list[str] | None = Query(default=None)`.

5. **Frontend `api.ts`** — `listAccomplishments(tag?)` and `listNotes(tag?)` must accept `tags?: string[]` and append multiple `?tag=` params.

6. **AccomplishmentListView / NoteListView** — replace `<select>` filter with `<TagInput allowCreate={false}>`. Replace plain tags `<input>` in forms with `<TagInput allowCreate={true}>`.

7. **AccomplishmentDetailView / NoteDetailView** — replace plain tags `<input>` with `<TagInput allowCreate={true}>`.
