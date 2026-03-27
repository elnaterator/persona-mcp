# Feature Specification: Personal Context Notes

**Feature Branch**: `013-personal-context-section`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "Rather than articles, call each file a note. We will manage personal notes. The top level section will also be called 'Notes', so we have 'Jobs' and 'Notes'."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Create Personal Notes (Priority: P1)

Users want to document personal information and experiences via a new "Notes" section alongside the existing "Jobs" section. This allows them to capture achievements, projects, skills, or any context not captured by job history. A note can be created with just a title, allowing users to fill in content incrementally.

**Why this priority**: This is the core feature. Without the ability to create and view notes, the entire section is non-functional. This is the MVP.

**Independent Test**: Can be fully tested by navigating to the Notes section, creating a note, viewing it, and verifying the data persists after a page refresh.

**Acceptance Scenarios**:

1. **Given** the user is viewing their personal context, **When** they access the Notes section, **Then** they see an empty state message or existing notes listed as summaries (title, tags, last modified date) with a button to create a new note
2. **Given** the user clicks "Create Note", **When** they enter a title (required) and optionally content and tags, **Then** the note is saved and displayed in the Notes list
3. **Given** the user submits a note without a title, **Then** the system rejects the request and returns a descriptive error indicating the title is required
4. **Given** the user has created notes, **When** they refresh the page, **Then** the notes are still visible
5. **Given** the user requests a specific note by ID, **When** the note exists, **Then** the full detail is returned including title, content, tags, and timestamps
6. **Given** the user requests a note that does not exist, **Then** the system returns a descriptive not-found error

---

### User Story 2 - Edit and Update Notes (Priority: P2)

Users need to modify existing notes to update information, fix typos, or expand on previous entries. This allows notes to evolve over time without recreating them.

**Why this priority**: Essential for usability. Users will inevitably want to edit their notes. This is a natural part of the CRUD lifecycle.

**Independent Test**: Can be fully tested by creating a note, clicking edit, changing the content, saving it, and verifying the changes persist.

**Acceptance Scenarios**:

1. **Given** a note exists, **When** the user clicks edit on that note, **Then** the note content becomes editable with title, content, and tag fields
2. **Given** the user is editing a note, **When** they make changes and click save, **Then** only the changed fields are updated and the note returns to view mode
3. **Given** the user is editing a note, **When** they click cancel, **Then** the edit is discarded and the original note is displayed
4. **Given** the user attempts to edit a non-existent note, **Then** the system returns a descriptive not-found error

---

### User Story 3 - Tag Notes (Priority: P2)

Users need to organize and categorize their notes using tags, enabling better organization and discoverability of related notes across their collection. Tags are free-form strings — users can type whatever makes sense to them. The system normalizes tags by trimming whitespace and lowercasing to prevent duplicates.

**Why this priority**: Important for usability and information organization. As the notes collection grows, tags become essential for managing and finding related content. This pairs with search functionality.

**Independent Test**: Can be fully tested by creating a note with tags, viewing the tags on the note, and editing tags on existing notes.

**Acceptance Scenarios**:

1. **Given** the user is creating or editing a note, **When** they add tags to the note, **Then** the tags are saved with the note
2. **Given** the user is typing a tag, **When** the input matches existing tags from the user's unified tag pool (notes and accomplishments), **Then** the system suggests matching tags via autocomplete
3. **Given** a note has multiple tags, **When** the user views the note, **Then** all tags are displayed clearly
4. **Given** the user adds a tag with mixed case (e.g., "Leadership"), **Then** the system normalizes it to lowercase ("leadership")
5. **Given** the user adds a tag with leading/trailing whitespace, **Then** the system trims the whitespace before saving

---

### User Story 4 - Delete Notes (Priority: P3)

Users need the ability to remove notes they no longer want to keep, whether due to inaccuracy, confidentiality, or simply cleaning up outdated information.

**Why this priority**: Important for data management but lower priority than creation, editing, and tagging. Most users will primarily create and update notes, with deletion being an occasional maintenance task.

**Independent Test**: Can be fully tested by creating a note, deleting it, and verifying it no longer appears in the notes list.

**Acceptance Scenarios**:

1. **Given** a note exists, **When** the user deletes it, **Then** the note is removed and no longer appears in list or fetch-by-id responses
2. **Given** the user attempts to delete a non-existent note, **Then** the system returns a descriptive not-found error

---

### User Story 5 - Search and Filter Notes (Priority: P2)

Users need to search their notes by keywords and filter by tags to quickly find relevant notes, especially as their note collection grows. Keyword search uses substring matching against title and content, and is case-insensitive. When multiple keywords are provided, all must match (AND logic).

**Why this priority**: Essential for usability when managing multiple notes. Search and filtering are critical for information retrieval and avoiding overwhelming lists.

**Independent Test**: Can be fully tested by creating multiple tagged notes, searching by keyword, filtering by tag, and verifying correct results appear.

**Acceptance Scenarios**:

1. **Given** the user is viewing the Notes section, **When** they enter keywords in a search box, **Then** only notes matching those keywords (in title or content) are displayed
2. **Given** the user is viewing the Notes section, **When** they select one or more tags to filter, **Then** only notes that have ALL selected tags are displayed (AND logic)
3. **Given** the user applies both keyword search and tag filters, **When** they do so simultaneously, **Then** results are the intersection of both filters
4. **Given** the user has no search results, **When** they view the empty state, **Then** a helpful message indicates no matches were found
5. **Given** the user enters multiple keywords (e.g., "python deployment"), **Then** only notes containing all keywords are shown

---

### User Story 6 - Access Notes via MCP (Priority: P3)

An AI assistant (such as Claude) uses the MCP server to read, write, and search notes on behalf of the user, enabling AI-powered workflows such as drafting content, organizing information, or retrieving relevant context.

**Why this priority**: MCP exposure is a core distribution channel for this project, but it layers on top of the underlying data capability already tested in P1-P5.

**Independent Test**: Can be tested by calling the MCP list, create, search, and get tools directly through the MCP interface and verifying correct responses without using the REST API or UI.

**Acceptance Scenarios**:

1. **Given** notes are stored, **When** an MCP client calls the list tool, **Then** all notes are returned as summaries (title, tags, timestamps)
2. **Given** an MCP client submits a new note, **When** the tool call completes, **Then** the entry is persisted and visible via the REST API and UI
3. **Given** an MCP client searches with keywords and/or tags, **Then** matching notes are returned with the same results as the REST API
4. **Given** an MCP tool call with invalid input (missing title), **Then** a structured error response is returned without unhandled exceptions

### Edge Cases

- What happens when a user creates a note with only whitespace in the title? (System rejects it with a descriptive error; title is required)
- What happens when a user creates a note with a title but no content? (System accepts it — content is optional to support incremental drafting)
- How does the system handle rapid successive creates/edits of notes? (Each operation is processed independently; last write wins)
- What happens when a user attempts to access notes on a slow connection? (UI shows loading state and does not lose data)
- How does the system handle when a note title or content exceeds reasonable length limits? (System enforces max length with clear feedback)
- What happens when a user adds a tag with leading/trailing whitespace? (System trims whitespace before saving)
- How does the system handle duplicate tags with different cases? (Tags are normalized to lowercase; "Python" and "python" are the same tag)
- What happens when a user adds a tag that is empty or becomes empty after trimming whitespace? (System ignores or rejects the empty tag without error, leaving the note unchanged)
- What happens when a user adds a tag that is already on the note? (System deduplicates silently; the tag appears only once)
- What happens when a search returns a very large number of results? (All results are returned; pagination is a future consideration)
- What happens when the user submits an empty search query? (System treats it as no filter and returns all notes, same as the unfiltered list)
- What happens when the user filters by a tag that no notes currently have? (System returns an empty state with a helpful "no matches" message — same behavior as any empty search result)
- What happens when a user requests a note ID that does not exist? (System returns a descriptive not-found error)

## Requirements *(mandatory)*

### Functional Requirements

#### Core Note Management
- **FR-001**: System MUST display a "Notes" section in the personal context UI alongside the "Jobs" section
- **FR-002**: System MUST allow users to create a new note with a required title, optional content/body, and optional tags
- **FR-003**: System MUST display all user notes in a list view as summaries (title, tags, last modified date), sorted reverse chronologically by last modified date
- **FR-004**: System MUST allow users to view the full details of a single note (title, content, tags, created and modified timestamps) by selecting it
- **FR-005**: System MUST allow users to edit an existing note's title, content, and tags without overwriting unchanged fields
- **FR-006**: System MUST allow users to delete a note by its unique identifier
- **FR-007**: System MUST persist all notes durably and retrieve them on subsequent visits
- **FR-008**: System MUST scope notes to the authenticated user (users can only see/edit/delete their own notes)
- **FR-009**: System MUST validate that note title is not empty or whitespace-only before saving; content is optional
- **FR-010**: System MUST maintain the same access control and authentication model as the existing Jobs and Accomplishments sections
- **FR-011**: System MUST return descriptive error messages when required fields are missing or an operation targets a non-existent note
- **FR-011a**: System MUST enforce a maximum title length of 255 characters and a maximum content length of 10,000 characters, returning a descriptive error when exceeded
- **FR-011b**: System MUST enforce a maximum tag length of 50 characters, returning a descriptive error when exceeded

#### Tagging
- **FR-012**: System MUST allow users to add multiple free-form text tags to a note during creation or editing, consistent with the accomplishments tagging model
- **FR-013**: System MUST normalize tags by trimming whitespace and lowercasing to prevent duplicates
- **FR-014**: System MUST allow users to remove individual tags from a note while preserving the note
- **FR-015**: System MUST display tags visually on notes in both list and detail views
- **FR-016**: System MUST provide tag autocomplete suggestions drawn from the user's unified tag pool (shared across notes and accomplishments) as the user types, enabling consistent taxonomy reuse across features

#### Search and Filtering
- **FR-017**: System MUST provide keyword search that matches against note title and content using case-insensitive substring matching
- **FR-018**: System MUST support a search parameter (e.g., `q`) consistent with the existing application list endpoint pattern
- **FR-019**: System MUST provide tag-based filtering to display only notes matching selected tags; when multiple tags are selected, results MUST include only notes that have ALL selected tags (AND logic)
- **FR-020**: System MUST support combining keyword search with tag filters, returning the intersection of results
- **FR-021**: System MUST treat multiple keywords as AND — all keywords must match for a note to appear in results
- **FR-022**: System MUST display a helpful empty state when search/filter returns no results

#### Interface Parity
- **FR-023**: System MUST expose all note CRUD operations via REST API endpoints, following the same route conventions as existing features
- **FR-024**: System MUST expose search, tag filtering, and tag listing operations via REST API
- **FR-025**: System MUST expose all note operations (list with search/filter, get, create, update, delete) via MCP tools, following the same naming and pattern conventions as existing tools
- **FR-026**: System MUST ensure consistent data and behavior across UI, API, and MCP interfaces
- **FR-027**: System MUST apply the same validation and authorization rules across all three interfaces (UI, API, MCP)

### Key Entities

- **Note**: Represents a single personal note entry. Key attributes: unique identifier, title (required), content (optional text), tags (list of free-form strings, stored as JSON array on the note — consistent with the accomplishments pattern), created timestamp (system-managed), last-modified timestamp (system-managed), owner (relationship to user). Used to store user-created personal context information outside of job history.
- **User**: Existing entity that notes relate to. Notes are scoped to a single user and cannot be accessed by other users.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a note and see it appear in the Notes list perceived as immediate after saving
- **SC-002**: Users can edit an existing note and have changes persist and be visible perceived as immediate
- **SC-003**: Users can delete a note and have it immediately removed from the list
- **SC-004**: 100% of operations include proper error handling with user-friendly messages for failures and descriptive not-found errors for missing records
- **SC-005**: All notes are properly scoped to the authenticated user with no cross-user access possible
- **SC-006**: Search and filter results appear perceived as immediate (under 500ms end-to-end) for a user's note collection of up to 500 notes
- **SC-007**: Users can add, edit, and remove tags from notes with changes persisting immediately
- **SC-008**: All functionality (create, edit, delete, search, filter, tag) works consistently across UI, REST API, and MCP interfaces — data created through any one interface is visible through the other two
- **SC-009**: Users can search/filter across all their notes using both keywords and tags simultaneously
- **SC-010**: 100% of MCP tool calls return structured responses (either data or a structured error); no unhandled exceptions are exposed to MCP clients

## Scope *(optional)*

### In Scope
- Create, read, update, and delete personal notes (title required, content optional)
- Free-form tagging system for notes with autocomplete suggestions from existing tags
- Keyword search across note titles and content (case-insensitive substring matching, AND for multiple keywords)
- Tag-based filtering and search
- Display Notes as a top-level section alongside Jobs
- User authentication and access control for notes
- Note list view (summaries) and detail view (full content) with tags displayed
- Input validation for notes and tags
- Full functionality across three interfaces: UI, REST API, and MCP
- Consistent behavior, validation, and authorization across all three interfaces

### Out of Scope
- Rich text editing (markdown or WYSIWYG editors)
- Bulk operations (multi-select delete, export, etc.)
- Sharing notes with other users
- Note versioning or history tracking
- Integration with external services
- Advanced search features (regex, fuzzy search, complex boolean queries)
- Note templates or note types
- Scheduled notes or reminders
- Pagination (future consideration if note volume warrants it)
- Unified AI context aggregation across notes, accomplishments, and applications (future feature)

## Assumptions

- Notes are simple text entries with a title and optional body (no formatting)
- Notes follow the same data ownership model as existing features (user-scoped)
- The backend infrastructure exists to support a new database table for notes
- No migration of existing data is required (this is a new feature)
- Authentication/authorization mechanisms already in place (Clerk) can be reused for notes
- Tags are stored as a JSON array on the note record, consistent with the accomplishments pattern
- Tags are created implicitly when added to a note — no separate tag management is needed
- Tag autocomplete draws from a unified pool shared across notes and accomplishments, enabling consistent taxonomy
- Display order in the list view is reverse chronological by last-modified timestamp
- The MCP tools follow the same naming and pattern conventions as existing tools (e.g., `list_notes`, `get_note`, `create_note`, `update_note`, `delete_note`); search is handled via `list_notes(q=, tag=)` parameters rather than a separate tool
- The REST API follows the same route structure conventions already in the project
- All three interfaces (UI, REST API, MCP) enforce the same business logic and validation rules
- Keyword search uses case-insensitive substring matching with AND logic for multiple terms, consistent with existing search patterns

## Dependencies

- Existing user authentication system (Clerk)
- Database connection pool and migration capabilities
- Existing frontend framework and component patterns (React, React Router v7)
- Existing REST API framework (FastAPI)
- Existing MCP server infrastructure (FastMCP)
- Same styling/component system as Jobs and Accomplishments sections for consistency

## Clarifications

### Session 2026-03-26

- Q: Should tags be validated to specific character sets (alphanumeric, hyphens, underscores only)? → A: No — tags are free-form strings consistent with the accomplishments feature. System normalizes by trimming whitespace and lowercasing.
- Q: Should the tag entity be a separate database table? → A: No — tags are stored as a JSON array on the note record, consistent with the accomplishments pattern.
- Q: Is note content required? → A: No — only title is required. Content is optional to support incremental drafting, consistent with how accomplishments allow partial STAR fields.
- Q: Should there be a delete confirmation dialog? → A: No — consistent with the accomplishments feature, delete is immediate without a confirmation step.
- Q: How are notes sorted in the list? → A: Reverse chronological by last-modified timestamp. No user-controlled sort options.
- Q: Should notes integrate into a broader AI context (alongside accomplishments and applications)? → A: Out of scope for this feature. Future work may add unified context aggregation.
- Q: How does keyword search work? → A: Case-insensitive substring matching using a `q` parameter, consistent with the existing application list endpoint. Multiple keywords use AND logic.
- Q: Should there be pagination? → A: Not in this iteration. All results are returned. Pagination is a future consideration.
- Q: Should tag autocomplete draw from notes-only or a shared pool across all features? → A: Shared pool across notes and accomplishments, enabling a unified taxonomy.
- Q: When filtering by multiple tags, should results use AND or OR logic? → A: AND — notes must have ALL selected tags. Consistent with keyword search AND behavior.
- Q: Should content length limits (title 255, content 10,000, tag 50) be formal requirements or just assumptions? → A: Formal functional requirements (FR-011a, FR-011b) to ensure validation is implemented and tested across all interfaces.
