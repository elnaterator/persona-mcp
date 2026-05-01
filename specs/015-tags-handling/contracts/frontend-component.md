# Frontend Component Contracts: Improved Tags Handling

**Feature**: 015-tags-handling  
**Date**: 2026-04-23

---

## New Component: TagInput

**File**: `frontend/src/components/TagInput.tsx`  
**CSS**: `frontend/src/components/TagInput.module.css`  
**Tests**: `frontend/src/__tests__/components/TagInput.test.tsx`

### Props

```typescript
interface TagInputProps {
  value: string[]                     // Currently committed tag chips
  onChange: (tags: string[]) => void  // Emits updated chips array
  availableTags: string[]             // Pool of existing tags for autocomplete
  allowCreate?: boolean               // Show "Create new tag: [text]" option (default: true)
  placeholder?: string                // Input placeholder text
  id?: string                         // For label association
}
```

### Behavior Contract

| Trigger                     | Action                                                                 |
|-----------------------------|------------------------------------------------------------------------|
| Type in input               | Show dropdown with matching `availableTags` (case-insensitive substring) |
| Press Enter or comma        | Commit typed text as chip (if non-empty after trim + lowercase)        |
| Press Escape                | Close dropdown; keep typed text                                        |
| Blur input                  | Commit non-empty typed text as chip; close dropdown                    |
| Click dropdown item         | Commit that tag as chip; clear input; close dropdown                   |
| Click "Create new tag: X"   | Commit X as chip; clear input; close dropdown                          |
| Click chip "×"              | Remove that chip                                                       |
| Attempt duplicate chip      | No-op (case-insensitive check against existing chips)                  |
| Type whitespace only        | Commit is no-op                                                        |

### Dropdown Content

When input text is non-empty:
1. Matching existing `availableTags` (exclude tags already in `value`)
2. If `allowCreate={true}`: always show "Create new tag: [normalized text]" as last option

When input text is empty: dropdown hidden.

### Tag Normalization on Commit

Before adding to `value`:
1. `trim()`
2. `.toLowerCase()`
3. Reject if empty
4. Reject if already in `value` (case-insensitive — but since all chips are lowercase, simple equality check suffices)

### Visual Structure

```
┌──────────────────────────────────────────────────────────┐
│ [chip: leadership ×] [chip: technical ×] [input........] │
└──────────────────────────────────────────────────────────┘
         ┌────────────────────────────────────────┐
         │ ✓ team leadership                      │
         │ ✓ technical writing                    │
         │ + Create new tag: "tech"               │
         └────────────────────────────────────────┘
```

CSS classes use existing design tokens:
- Chip: `background-color: var(--accent-green-bg); color: var(--accent-green)` (matches existing `.tagBadge`)
- Input: same as existing `.metaInput` / `.input` styles
- Dropdown: `background-color: var(--bg-hover); border: 1px solid var(--border-primary)`

---

## Updated: AccomplishmentListView

**Change 1 — Create form tags field**: Replace plain `<input type="text">` + `<datalist>` with:
```tsx
<TagInput
  value={form.tags}          // string[] instead of string
  onChange={(tags) => handleFieldChange('tags', tags)}
  availableTags={allTags}
  allowCreate={true}
  placeholder="Add tag..."
/>
```
`FormState.tags` changes from `string` to `string[]`. Remove comma-split parsing in `handleSave`.

**Change 2 — Filter**: Replace `<select>` with:
```tsx
<TagInput
  value={tagFilter}          // string[] instead of string
  onChange={setTagFilter}
  availableTags={allTags}
  allowCreate={false}
  placeholder="Filter by tag..."
/>
```
`tagFilter` state changes from `string` to `string[]`. `listAccomplishments(tagFilter)` → `listAccomplishments(tagFilter)` (now passes `string[]`).

---

## Updated: NoteListView

Same changes as AccomplishmentListView — both form tags field and filter field.

---

## Updated: AccomplishmentDetailView

**Edit form tags field**: Replace:
```tsx
<input type="text" value={editForm.tags.join(', ')} onChange={...} />
```
With:
```tsx
<TagInput
  value={(editForm.tags as string[]) ?? []}
  onChange={(tags) => handleEditFieldChange('tags', tags)}
  availableTags={allTags}
  allowCreate={true}
/>
```
`allTags` must be loaded (fetch `listAccomplishmentTags()` on mount, or pass down from parent — simplest: fetch locally on `startEdit`).

---

## Updated: NoteDetailView

Same change as AccomplishmentDetailView — replace plain tags input with `TagInput`.

---

## Updated: api.ts

```typescript
// Before
export async function listAccomplishments(tag?: string, q?: string): Promise<AccomplishmentSummary[]>

// After
export async function listAccomplishments(tags?: string[], q?: string): Promise<AccomplishmentSummary[]>
```

Implementation:
```typescript
const params = new URLSearchParams()
if (tags) tags.forEach(t => params.append('tag', t))
if (q) params.set('q', q)
```

Same change for `listNotes`.
