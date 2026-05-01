# Feature Specification: Improved Tags Handling

**Feature Branch**: `feat-015-tags-handling`  
**Created**: 2026-04-23  
**Status**: Draft  
**Last Clarified**: 2026-04-23  
**Input**: User description: "Improve tags handling: adding tags input text should recommend tags as you type; when adding tag (on space), should show label style bubble with x to remove; should always show option to create new tag using current typed text; in tag search, should behave similarly to filter by tags; when searching multiple tags, should require ALL tags"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tag Input with Autocomplete and Chip UI (Priority: P1)

A user is adding or editing an accomplishment or note. They click into the tags field and start typing. As they type, a dropdown appears suggesting existing tags that match. When the user presses Enter or comma, or selects a suggestion, the typed text becomes a styled chip/bubble with an "×" button. Multi-word tags (e.g., "soft skills", "team leadership") are supported. The user can remove any chip by clicking "×". The dropdown always includes an option to create a new tag using the current typed text, even if the text matches an existing tag exactly.

**Why this priority**: This is the core UX improvement. The current plain text comma-separated input is error-prone and invisible. Chip-based input gives immediate feedback, makes each tag distinct, and reduces typos.

**Independent Test**: Open any form with a tags field. Type a partial tag name — suggestions appear. Press Enter — a chip appears. Click "×" on chip — chip removed. Submit form — only chips become the saved tags.

**Acceptance Scenarios**:

1. **Given** the tags field is empty and existing tags exist, **When** the user types at least one character, **Then** a dropdown appears listing matching existing tags
2. **Given** the user has typed text in the tags field, **When** the user presses Enter or comma, **Then** the typed text is committed as a chip and the input clears
3. **Given** a chip is visible in the tags field, **When** the user clicks the "×" button on the chip, **Then** the chip is removed
4. **Given** the user has typed any non-empty text in the tags field, **When** the dropdown is open, **Then** an option to "Create new tag: [typed text]" is always visible regardless of whether matching tags exist
5. **Given** the user selects an existing tag from the dropdown, **When** the selection is made, **Then** it becomes a chip and the input clears
6. **Given** a tag chip already exists in the field, **When** the user types the same tag and commits it, **Then** the duplicate is not added

---

### User Story 2 - Multi-Tag Filter with AND Logic (Priority: P2)

A user is browsing the accomplishments or notes list and wants to filter by multiple tags simultaneously. Instead of a single-select dropdown, the filter area uses the same chip-based multi-select UI as the tag input. Each selected filter tag appears as a chip with an "×" to remove. Suggestions match existing tags as the user types. Only items that have ALL selected filter tags are shown.

**Why this priority**: The current single-select dropdown allows filtering by only one tag at a time. Multi-tag AND filtering solves this directly without requiring navigation away from the list.

**Independent Test**: On the list view, add two filter tag chips. Verify only items tagged with both tags appear. Remove one filter chip — items tagged with only the remaining tag reappear.

**Acceptance Scenarios**:

1. **Given** the filter tag input is empty, **When** the user types a tag name, **Then** matching existing tags appear as suggestions
2. **Given** one filter tag chip is active, **When** the user adds a second filter tag chip, **Then** only items tagged with BOTH tags are displayed
3. **Given** two filter tag chips are active, **When** the user clicks "×" on one chip, **Then** the list updates to show items matching only the remaining tag
4. **Given** no filter tags are active, **When** the list is displayed, **Then** all items are shown (unfiltered)
5. **Given** filter tag chips are active, **When** no items match ALL selected tags, **Then** an empty-state message is shown

---

### Edge Cases

- What happens when the user types in the tags field and presses Space? (Space does NOT commit — it is a normal character to allow multi-word tags)
- What happens when the user types a tag with leading or trailing spaces? (Trim whitespace before committing)
- What happens when the tags input field loses focus with unconfirmed text? (Commit non-empty text as a chip on blur)
- What happens when the tag dropdown is open and the user presses Escape? (Close the dropdown, keep typed text)
- What happens when a filter tag is selected that matches no items? (Show empty state with message)
- What happens when the user tries to create a tag with only whitespace? (Do not commit — treat as empty, no-op)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tags input MUST display matching existing tags in a dropdown as the user types (autocomplete)
- **FR-002**: The tags input MUST always include a "Create new tag: [typed text]" option in the dropdown when the input is non-empty
- **FR-003**: Pressing Enter or comma in the tags input MUST commit the current typed text as a removable chip. Multi-word tags are supported
- **FR-004**: Selecting a tag from the dropdown MUST commit it as a removable chip and clear the input
- **FR-005**: Each chip in the tags input MUST have an "×" control that removes only that chip when clicked
- **FR-006**: The tags input MUST prevent duplicate tag chips (case-insensitive; same tag cannot be added twice to the same field)
- **FR-013**: Tags MUST be normalized to lowercase on commit (e.g., "Leadership" becomes "leadership")
- **FR-007**: Committing empty or whitespace-only text in the tags input MUST be a no-op
- **FR-008**: The tag filter on list views MUST use the same chip-based multi-select input as the tags input
- **FR-009**: When multiple tag chips are active in the filter, the list MUST show only items that have ALL of the selected tags (AND logic, filtered server-side)
- **FR-010**: The tag filter MUST NOT show the "Create new tag" option (filter selects from existing tags only)
- **FR-011**: The tags input and tag filter MUST work consistently across Accomplishments and Notes views
- **FR-012**: Removing all filter tag chips MUST restore the full unfiltered list

### Key Entities

- **Tag**: A lowercase label string associated with an accomplishment or note. Tags are not a standalone entity — they exist only as values on their parent records. The pool of known tags is derived from existing records. All tags are normalized to lowercase on input.
- **Tag Chip**: A visual representation of a committed tag within an input or filter field, showing the tag label and a removal control.
- **Tag Suggestion**: A matching existing tag surfaced in the autocomplete dropdown while the user is typing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add a tag to a record in 2 or fewer interactions after seeing it in autocomplete (type partial + select, or type + Enter/comma)
- **SC-002**: Users can remove any individual tag chip without clearing the entire tags field
- **SC-003**: Users can filter a list by multiple tags simultaneously without navigating away or reloading the page
- **SC-004**: The tag input prevents duplicate tags from being saved to a record
- **SC-005**: Filtering with multiple tags (AND logic) excludes any item missing even one of the selected filter tags
- **SC-006**: The chip-based tag UI is visually and behaviorally consistent between the tag input (forms) and the tag filter (list views)

## Clarifications

### Session 2026-04-23

- Q: Space commits tags as chips, but this prevents multi-word tags (e.g., "soft skills"). Which commit trigger? → A: Only Enter and comma commit. Multi-word tags allowed.
- Q: Multi-tag AND filtering — server-side or client-side? → A: Server-side. Backend accepts multiple `tag` query params with AND logic.
- Q: Tag case sensitivity for dedup and storage? → A: Case-insensitive. Always convert to lowercase on commit.

## Assumptions

- Enter and comma are the commit triggers (not Space, to allow multi-word tags like "soft skills")
- On blur (focus lost), non-empty typed text is committed as a chip rather than discarded
- The "Create new tag" option creates the tag by associating it with the record on save — no standalone tag management flow exists
- Autocomplete suggestions perform a case-insensitive substring match. All tags are normalized to lowercase on commit
- The filter does not include a "Create new tag" option — users filter by existing tags only
- Multi-tag AND filtering is server-side: the backend accepts multiple `tag` query parameters and applies AND logic. This is a backend change (no new endpoints, but existing list endpoints accept repeated `tag` params)
