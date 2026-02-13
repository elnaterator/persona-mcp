# Feature Specification: Resume Web User Interface

**Feature Branch**: `feat-005-user-interface`
**Created**: 2026-02-12
**Status**: Draft
**Input**: User description: "React SPA user interface served from the same FastAPI server and container, with frontend/backend directory restructure and separate Makefiles"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Complete Resume (Priority: P1)

A user navigates to the web interface at the root URL and sees their complete resume displayed in a clean, readable format. All resume sections — contact information, summary, work experience, education, and skills — are rendered in a structured layout that resembles a traditional resume.

**Why this priority**: Viewing the resume is the foundational interaction. Without a readable display, editing features have no context. This delivers immediate value by providing a visual representation of stored resume data.

**Independent Test**: Can be fully tested by loading the root URL in a browser and verifying all resume sections render correctly with real data, delivering a readable resume view.

**Acceptance Scenarios**:

1. **Given** a resume with populated data, **When** the user navigates to the root URL, **Then** all resume sections are displayed in a structured, readable layout.
2. **Given** a resume with some empty sections, **When** the user views the resume, **Then** populated sections display their content and empty sections show a prompt or placeholder encouraging the user to add data.
3. **Given** a resume with multiple work experience entries, **When** the user views the experience section, **Then** entries are displayed in order with all fields (title, company, dates, location, highlights) visible.

---

### User Story 2 - Edit Contact Information and Summary (Priority: P2)

A user wants to update their contact details (name, email, phone, location, LinkedIn, website, GitHub) or professional summary. They click an edit control on the relevant section, make changes in an inline form, and save. The updated information is immediately reflected in the resume view.

**Why this priority**: Contact info and summary are single-value sections that are simpler to edit than list-based sections. This establishes the core edit-save pattern that all other editing builds upon.

**Independent Test**: Can be fully tested by editing contact fields and summary text, saving, and verifying changes persist after page reload.

**Acceptance Scenarios**:

1. **Given** the resume is displayed, **When** the user activates edit mode on the contact section, **Then** an editable form appears with the current contact field values pre-filled.
2. **Given** the user has modified contact fields, **When** they save the changes, **Then** the resume view updates to show the new values and a success confirmation is shown.
3. **Given** the user has modified the summary text, **When** they save, **Then** the updated summary is displayed and persists on page reload.
4. **Given** the user is editing a section, **When** they cancel without saving, **Then** the original values are restored and no changes are persisted.
5. **Given** the user submits invalid data (e.g., empty required fields), **When** they attempt to save, **Then** a clear validation error is shown and the save is prevented.

---

### User Story 3 - Manage List-Based Resume Entries (Priority: P3)

A user wants to add, edit, or remove entries in list-based resume sections: work experience, education, and skills. They can add new entries, modify existing ones, and delete entries they no longer want. Each operation provides clear feedback and the resume view updates accordingly.

**Why this priority**: List-based editing is more complex but essential for a complete resume management experience. It builds on the edit pattern established in P2 and covers the remaining data types.

**Independent Test**: Can be fully tested by adding a new experience entry, editing an existing education entry, removing a skill, and verifying all changes persist.

**Acceptance Scenarios**:

1. **Given** the experience section is displayed, **When** the user chooses to add a new entry, **Then** a form appears with fields for title, company, start date, end date, location, and highlights.
2. **Given** the user fills out a new entry form with valid data, **When** they save, **Then** the new entry appears in the section and a success confirmation is shown.
3. **Given** an existing education entry, **When** the user activates edit mode on that entry, **Then** a form appears pre-filled with the entry's current values.
4. **Given** the user has edited an entry, **When** they save, **Then** the updated values are displayed in the resume view.
5. **Given** an existing skill entry, **When** the user chooses to delete it and confirms the deletion, **Then** the entry is removed from the resume view.
6. **Given** the user attempts to add an entry with missing required fields, **When** they try to save, **Then** validation errors indicate which fields need attention.

---

### User Story 4 - Responsive Error Handling (Priority: P4)

When something goes wrong — the server is unavailable, a save operation fails, or data cannot be loaded — the user sees a clear, helpful error message rather than a broken or blank interface.

**Why this priority**: Error handling ensures the interface remains trustworthy and usable even when issues occur. It is important but secondary to core view and edit functionality.

**Independent Test**: Can be tested by simulating server errors and verifying appropriate error messages appear without breaking the interface.

**Acceptance Scenarios**:

1. **Given** the server is unavailable, **When** the user loads the page, **Then** a clear error message is displayed explaining the issue with a retry option.
2. **Given** a save operation fails due to a server error, **When** the user attempts to save, **Then** an error message is displayed and the user's unsaved changes are preserved in the form.
3. **Given** a network interruption occurs during data loading, **When** the page partially loads, **Then** sections that failed to load show individual error states without affecting successfully loaded sections.

---

### User Story 5 - Unified Serving from Single Origin (Priority: P1)

A user accesses the application from a single URL. The root path serves the web interface, while the existing API and MCP endpoints remain available at their current paths. Everything runs from a single container and server, so there are no cross-origin issues or multiple services to manage.

**Why this priority**: Serving everything from one origin simplifies deployment, eliminates CORS complexity, and provides a seamless user experience. This is a foundational architectural requirement that all other stories depend on.

**Independent Test**: Can be tested by accessing the root URL to load the interface, then verifying that API calls from the interface to existing endpoints succeed without cross-origin errors.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** a user navigates to the root path, **Then** the web interface loads.
2. **Given** the web interface is loaded, **When** the interface makes requests to existing API endpoints, **Then** the requests succeed without cross-origin errors.
3. **Given** the application is running, **When** a user navigates to existing API or MCP paths, **Then** those endpoints continue to function as before.

---

### User Story 6 - Monorepo Build and Development Workflow (Priority: P1)

A developer working on the project can build and run both frontend and backend from a single top-level command. The project is organized with separate `frontend/` and `backend/` directories, each with its own Makefile. A root Makefile orchestrates builds in the proper order so that running a single command produces a fully operational application.

**Why this priority**: Developer experience and build workflow are foundational — without a clear build process, no other features can be developed or tested effectively.

**Independent Test**: Can be tested by cloning the repo and running the root-level build command, then verifying the application starts and serves both the interface and API.

**Acceptance Scenarios**:

1. **Given** a fresh checkout of the repository, **When** a developer runs the root-level build command, **Then** both frontend and backend are built in the correct order.
2. **Given** the frontend has been built, **When** the backend starts, **Then** it serves the built frontend assets at the root path.
3. **Given** a developer is working on the frontend only, **When** they run the frontend Makefile targets, **Then** they can build, lint, and test the frontend independently.
4. **Given** a developer is working on the backend only, **When** they run the backend Makefile targets, **Then** they can lint, test, and run the backend independently.
5. **Given** the project is containerized, **When** a developer builds the container, **Then** the container includes both compiled frontend assets and the backend server, served from a single process.

---

### Edge Cases

- What happens when the resume has no data at all (completely empty)? The interface should display a welcoming empty state with prompts to start adding resume content.
- What happens when the user rapidly clicks save multiple times? The system should prevent duplicate submissions and only process one save operation at a time.
- What happens when two browser tabs are open and the user edits in both? The most recent save wins; the interface should reflect the latest server state on reload.
- What happens when the user enters very long text in a field (e.g., a 5000-character summary)? The form should handle long text gracefully with appropriate input sizing.
- What happens when the user's session or connection drops mid-edit? Unsaved form data should not be silently lost; the user should be notified of the failure.
- What happens when the frontend assets have not been built? The server should start but the root path should return a clear error or instruction rather than crashing.
- What happens when a developer runs backend tests without building the frontend first? Backend tests should pass independently without requiring frontend build artifacts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display all resume sections (contact, summary, experience, education, skills) in a single-page layout served from the root path.
- **FR-002**: System MUST allow users to edit contact information fields (name, email, phone, location, LinkedIn, website, GitHub) through an inline form.
- **FR-003**: System MUST allow users to edit the professional summary text through an inline form.
- **FR-004**: System MUST allow users to add new entries to list-based sections (experience, education, skills).
- **FR-005**: System MUST allow users to edit existing entries in list-based sections.
- **FR-006**: System MUST allow users to remove entries from list-based sections with a confirmation step.
- **FR-007**: System MUST validate user input before submission and display clear, field-level error messages for invalid data.
- **FR-008**: System MUST show a loading state while data is being fetched or saved.
- **FR-009**: System MUST show success confirmation after a successful save operation.
- **FR-010**: System MUST show error messages when server operations fail, without losing the user's unsaved changes.
- **FR-011**: System MUST display an empty state with guidance when a resume section has no data.
- **FR-012**: System MUST allow users to cancel an in-progress edit and revert to the previously saved values.
- **FR-013**: System MUST be usable on both desktop and mobile screen sizes.
- **FR-014**: System MUST serve the web interface and all API/MCP endpoints from a single server process and container.
- **FR-015**: System MUST serve the web interface from the root path (`/`) without conflicting with existing API and MCP endpoint paths.
- **FR-016**: System MUST support a project directory structure with separate `frontend/` and `backend/` directories at the repository root.
- **FR-017**: System MUST provide a root-level build command that builds frontend and backend in the correct order.
- **FR-018**: System MUST provide separate build, lint, and test commands for frontend and backend that can run independently.

### Key Entities

- **Resume**: The complete document containing all sections. Displayed as a single-page view.
- **Contact Information**: A single set of personal details — name, email, phone, location, and professional profile links (LinkedIn, website, GitHub).
- **Summary**: A free-text professional summary or objective statement.
- **Work Experience Entry**: A single job record with title, company, start/end dates, location, and a list of highlights/accomplishments.
- **Education Entry**: A single education record with institution, degree, field of study, start/end dates, and honors.
- **Skill Entry**: A named skill with an optional category grouping.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view their complete resume within 3 seconds of opening the interface.
- **SC-002**: Users can complete an edit to any single section (from clicking edit to seeing the saved result) in under 30 seconds.
- **SC-003**: 95% of users can successfully add a new work experience entry on their first attempt without external guidance.
- **SC-004**: All form validation errors are visible and understandable without scrolling or navigating away from the form.
- **SC-005**: The interface is fully functional on screens as small as 375px wide (standard mobile) and up to 1920px wide (standard desktop).
- **SC-006**: Users receive visual confirmation of all save and delete operations within 2 seconds of the action.
- **SC-007**: A developer can build and start the complete application from a fresh checkout using a single root-level command.
- **SC-008**: The entire application (frontend interface + backend API + MCP server) runs as a single container with a single entry point.

## Clarifications

### Session 2026-02-12

- Q: What frontend technology should be used for the UI? → A: React SPA with separate build toolchain (Node.js/npm)
- Q: Where should the frontend live and how is it served in production? → A: Monorepo restructure with `frontend/` and `backend/` top-level directories. The React SPA is built to static assets and served by the same FastAPI server from the root path `/`. Everything runs in a single container.
- Q: How should build tooling be organized? → A: Separate Makefiles for frontend and backend directories, with a root Makefile that orchestrates builds in the proper order.

## Assumptions

- The frontend is a React single-page application (SPA) with its own build toolchain.
- The project is restructured into a monorepo with two top-level directories: `frontend/` (React app) and `backend/` (Python server). Existing `src/backend/` code moves to `backend/src/persona/` (the Python package is renamed from `backend` to `persona` to avoid redundant nesting).
- The frontend is built to static assets that are served by the FastAPI backend from the root path (`/`). The frontend and backend run as a single server process in a single container.
- Each directory (`frontend/`, `backend/`) has its own Makefile for independent development tasks. A root Makefile orchestrates building both in the correct order (frontend first, then backend copies/serves the built assets).
- This is a single-user personal resume tool; no authentication or multi-user access control is required for this feature.
- The existing server and data endpoints are available and functioning; this feature consumes them but does not modify their behavior.
- Since the frontend is served from the same origin as the API, no CORS configuration is needed for frontend-to-API communication.
- Skills are displayed grouped by category when categories are present.
- Date fields in experience and education entries accept free-text input (e.g., "Jan 2020", "2020") rather than requiring a specific date format, consistent with the existing data model.
