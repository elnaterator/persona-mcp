# Feature Specification: Job Application Management

**Feature Branch**: `006-job-applications`
**Created**: 2026-02-17
**Updated**: 2026-02-17
**Status**: Draft (rev 3)
**Input**: User description: "Manage job applications via MCP, REST API, and UI for AI-assisted resume tuning, communication drafting, and contact tracking"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Track Job Applications (Priority: P1)

A job seeker creates a new job application entry by providing the company name, position title, and job description. They can view all their applications in a list, see details for each one, update the status as they progress through the hiring pipeline, and delete applications they no longer want to track. Each application can optionally be associated with a resume version.

**Why this priority**: This is the foundational entity — nothing else (contacts, communications) works without a job application to attach to. It delivers immediate organizational value even without AI features.

**Independent Test**: Can be fully tested by creating an application, viewing it in a list, updating its status, and verifying the data persists. Delivers value as a standalone job tracking tool.

**Acceptance Scenarios**:

1. **Given** no applications exist, **When** the user creates an application with company name, position title, and job description text, **Then** the application is saved and appears in the applications list with a default status of "Interested" and no associated resume version
2. **Given** an application exists, **When** the user views the application details, **Then** all stored fields are displayed including company, position, job description, status, creation date, and the associated resume version (if any)
3. **Given** an application exists with status "Interested", **When** the user updates the status to "Applied", **Then** the status change is persisted and reflected in the list view
4. **Given** multiple applications exist, **When** the user views the applications list, **Then** applications are displayed sorted by most recently updated, with status visible for each
5. **Given** an application exists, **When** the user deletes it, **Then** the application and all associated contacts and communications are removed. Any associated resume version is NOT deleted (it may be used by other applications).

---

### User Story 2 - Manage Contacts for a Job Application (Priority: P2)

A job seeker adds contacts (recruiters, hiring managers, interviewers) to a specific job application. Each contact has a name, role/title, email, phone, and optional notes. Contacts help the user remember who they've spoken with and provide context for AI-assisted communication drafting.

**Why this priority**: Contacts are the bridge between passive tracking (Story 1) and active communication (Story 3). They're needed before communications make sense, and they're simpler to implement than resume versions.

**Independent Test**: Can be fully tested by adding a contact to an application, viewing the contacts list, editing a contact's details, and removing a contact. Delivers value as a contact organizer for each application.

**Acceptance Scenarios**:

1. **Given** an application exists, **When** the user adds a contact with name and email, **Then** the contact appears in the application's contacts list
2. **Given** a contact exists for an application, **When** the user updates the contact's role or notes, **Then** the changes are persisted
3. **Given** a contact exists for an application, **When** the user removes the contact, **Then** it no longer appears in the contacts list
4. **Given** an application has multiple contacts, **When** the user views the application details, **Then** all contacts are listed with their name, role, and email visible

---

### User Story 3 - Track Communications for a Job Application (Priority: P3)

A job seeker logs communications (emails sent, emails received, phone call notes, interview notes) associated with a specific job application. Each communication record includes a type, subject, body/content, date, direction (sent/received), a status (draft, ready, sent, archived), and optionally which contact it was with. This history provides context for AI to draft future communications. Communications progress through a status workflow: AI or the user creates a draft, the user marks it ready for sending, then marks it sent after actually sending, and can archive old communications.

**Why this priority**: Communication history is essential context for the AI-assisted drafting feature (Story 5). Without stored communications, AI has no basis for tone, context, or follow-up content. It also delivers standalone value as a communication log.

**Independent Test**: Can be fully tested by adding a communication entry to an application, viewing the communication timeline, editing an entry, and transitioning it through statuses (draft → ready → sent). Delivers value as a communication log even without AI features.

**Acceptance Scenarios**:

1. **Given** an application exists, **When** the user adds a communication with type "email", direction "sent", subject, and body, **Then** the communication appears in the application's timeline sorted by date with a default status of "sent" (for manually logged communications)
2. **Given** a communication exists, **When** the user views it, **Then** all fields are displayed including type, direction, subject, body, date, status, and associated contact (if any)
3. **Given** multiple communications exist for an application, **When** the user views the application's communication timeline, **Then** entries are displayed in reverse chronological order with status badges visible
4. **Given** a communication exists, **When** the user edits the body text, **Then** the changes are persisted
5. **Given** a communication with status "draft", **When** the user marks it as "ready", **Then** the status changes to "ready" and is visually distinguished in the timeline
6. **Given** a communication with status "ready", **When** the user marks it as "sent", **Then** the status changes to "sent"
7. **Given** a communication with status "sent", **When** the user archives it, **Then** the status changes to "archived"

---

### User Story 4 - Manage Resumes (Priority: P4)

A job seeker manages multiple resume versions, each a complete resume with contact info, summary, experience, education, and skills. There is no separate "master resume" — the system maintains a list of resume versions, and exactly one is marked as the **default**. The default resume is the one displayed and used as the primary resume (e.g., shown in the main resume view, used as the template when creating new versions). The user can change which version is the default at any time. All resume versions support full editing capabilities: updating contact info and summary, and adding, editing, removing, and reordering experience entries, education entries, and skills. Resume versions can be associated with job applications — each application has at most one associated resume version, and a single resume version can be shared across multiple applications (e.g., a "Technical Focus" resume used for all engineering roles). Creating a new resume version initializes it as a copy of the current default resume. Via MCP, an AI assistant can read a job description and the default resume to create a tailored resume version.

**Why this priority**: This is the core AI-assisted value proposition, but it depends on the application entity (Story 1) and benefits greatly from having the job description already stored. It's ranked P4 because the data foundation (Stories 1-3) should exist first.

**Independent Test**: Can be fully tested by viewing the resumes list, creating a new resume version (verifying it copies the default), editing the new version's sections, changing which version is the default, and associating a version with an application.

**Acceptance Scenarios**:

1. **Given** a default resume exists, **When** the user creates a new resume version with a label, **Then** a copy of the default resume is created as a new resume version visible in the resumes list, and the new version is NOT marked as default
2. **Given** a resume version exists, **When** the user modifies its summary, adds an experience entry, or reorders skills, **Then** the changes are saved to that version without affecting any other resume version
3. **Given** multiple resume versions exist, **When** the user views the resumes list, **Then** all versions are displayed with labels, creation dates, the number of applications using each, and a clear indicator of which is the default
4. **Given** multiple resume versions exist, **When** the user marks a different version as the default, **Then** the previously default version loses its default status and the newly selected version becomes the default
5. **Given** a resume version and an application both exist, **When** the user associates the resume version with the application, **Then** the application shows the linked resume version in its detail view
6. **Given** a resume version is associated with multiple applications, **When** the user views any of those applications, **Then** each shows the same linked resume version
7. **Given** an application has an associated resume version, **When** the user removes the association, **Then** the application no longer shows a linked resume version, but the resume version itself is not deleted
8. **Given** a job description, **When** an AI assistant is asked via MCP to create a tailored resume, **Then** the AI can read the default resume and produce a tailored resume version that can be associated with the relevant application
9. **Given** no resume versions exist, **When** the user creates their first resume version, **Then** it is automatically marked as the default

---

### User Story 5 - AI-Assisted Communication Drafting (Priority: P5)

A job seeker asks an AI assistant (via MCP) to draft a communication — such as a follow-up email after an interview, a thank-you note, or an initial outreach message. The AI has access to the job description, the contact's details, past communications, and the user's default resume to produce a contextually relevant draft. The draft is stored as a new communication entry with status "draft" that the user can review, edit, mark as "ready", and eventually mark as "sent" after sending.

**Why this priority**: This is the second major AI-powered feature and depends on all previous stories being in place (application, contacts, communications history, and ideally a tailored resume). It delivers high value but requires the most context to work well.

**Independent Test**: Can be fully tested by invoking the MCP tool with an application ID and communication type, verifying the AI has access to all relevant context (job description, contacts, past communications), and confirming a draft communication is returned/stored. The user can then edit and progress it through statuses.

**Acceptance Scenarios**:

1. **Given** an application with a job description, at least one contact, and prior communication history, **When** an AI assistant is asked to draft a follow-up email via MCP, **Then** the AI produces a draft that references relevant context from the job description and prior communications
2. **Given** the AI produces a draft communication, **When** the draft is stored, **Then** it appears in the application's communication timeline with status "draft"
3. **Given** a draft communication exists, **When** the user reviews and marks it as "ready", **Then** the communication status changes to "ready"

---

### Edge Cases

- What happens when the user creates their first resume version with no existing versions? The system creates the version with the provided data (or empty if no data provided) and automatically marks it as the default.
- What happens when the user tries to delete the default resume version? If it is the only resume version, the system prevents deletion (there must always be at least one resume version that is the default). If other versions exist, the system deletes it and automatically promotes another version (the most recently updated) to default.
- What happens when the user tries to set the default to a version that is already the default? The system treats it as a no-op and returns success.
- What happens when an application is deleted that has associated contacts and communications? All associated contacts and communications are cascade-deleted. The application's association with its resume version is removed, but the resume version itself is NOT deleted (it may be shared with other applications).
- What happens when a resume version is deleted that is associated with applications? The association is removed from all linked applications (they revert to having no resume version). The applications themselves are not affected.
- What happens when the user adds a communication referencing a contact that has since been deleted? The communication retains the contact name in a denormalized `contact_name` field (populated at creation time) but the `contact_id` link is set to null.
- How does the system handle very long job descriptions (e.g., pasted from a job board)? The system accepts job descriptions up to 50,000 characters to accommodate verbose postings.
- What happens when the user tries to create a duplicate application (same company and position)? The system allows it — users may re-apply to the same position at a different time.
- What happens when a communication has status "draft" and the user tries to set it to "archived"? Communication status transitions are free-form — any status can change to any other status. The UI may suggest logical progressions but does not enforce them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to create, read, update, and delete job applications with company name, position title, job description, status, source/URL, notes, and optional resume version association
- **FR-002**: System MUST support application status tracking with at minimum these statuses: Interested, Applied, Phone Screen, Interview, Offer, Accepted, Rejected, Withdrawn. Status transitions are free-form — any status may change to any other status without validation constraints
- **FR-003**: System MUST allow users to add, update, and remove contacts associated with a specific application, including name, role/title, email, phone, and notes
- **FR-004**: System MUST allow users to add, update, and remove communication entries associated with a specific application, including type (email, phone, interview note, other), direction (sent/received), subject, body, date, status, and optional contact reference
- **FR-005**: System MUST support communication statuses: draft, ready, sent, archived. Status transitions are free-form. Default status for manually added communications is "sent"; default for AI-generated communications is "draft"
- **FR-006**: System MUST manage resumes as a list of resume versions (no separate "master resume" concept). Each resume version is a complete, independent resume containing contact info, summary, experience, education, and skills
- **FR-007**: System MUST allow full CRUD operations on each resume version's sections, including updating contact info and summary, and adding, removing, reordering, and editing experience entries, education entries, and skills
- **FR-008**: System MUST expose all functionality (resumes, applications, contacts, communications) through MCP tools, REST API endpoints, and the web UI with consistent behavior
- **FR-009**: System MUST cascade-delete all associated contacts and communications when an application is deleted. Resume version associations are removed but the resume version itself is preserved
- **FR-010**: System MUST provide MCP tools that allow an AI assistant to read all context for a given application (job description, contacts, communications, associated resume version, default resume) in a single operation
- **FR-011**: System MUST store communication drafts produced by AI assistants as communications with status "draft" linked to the appropriate application
- **FR-012**: System MUST sort applications by most recently updated and communications by date in reverse chronological order
- **FR-013**: System MUST support filtering the applications list by status and searching by company name or position title
- **FR-014**: System MUST allow associating a resume version with an application and removing that association. Each application has at most one associated resume version. One resume version may be associated with many applications
- **FR-015**: System MUST allow users to view a list of all resume versions with labels, creation dates, the count of applications using each version, and a clear indicator of which is the default
- **FR-016**: System MUST allow users to delete a resume version, which removes the association from all linked applications but does not delete the applications themselves. The system MUST prevent deletion of the default resume version if it is the only version
- **FR-017**: System MUST maintain exactly one resume version as the default at all times. The user can change the default designation. Creating a new resume version copies the current default resume's data. If the default is deleted (when other versions exist), the system automatically promotes the most recently updated version
- **FR-018**: System MUST allow creating a new resume version initialized as a copy of the current default resume. The new version is not marked as default unless it is the first version created
- **FR-019**: System MUST replace the existing single-resume API with resume version APIs. All resume editing operations (update contact, update summary, add/edit/remove/reorder entries for experience, education, skills) MUST operate on a specific resume version identified by ID

### Key Entities

- **Job Application**: The central entity representing a specific job opportunity being pursued. Contains company name, position title, job description text, application status, source URL, notes, optional reference to a resume version, and timestamps. Has one-to-many relationships with contacts and communications. Has an optional many-to-one relationship with resume version.
- **Application Contact**: A person associated with a job application (recruiter, hiring manager, interviewer). Contains name, role/title, email, phone, and notes. Belongs to exactly one application.
- **Communication**: A logged interaction related to a job application (email, phone call, interview notes). Contains type, direction, subject, body, date, status (draft/ready/sent/archived), denormalized contact name, and optional reference to a contact. Belongs to exactly one application.
- **Resume Version**: A complete, independent resume. Contains contact info, summary, experience, education, and skills — the same structure as the existing resume but stored per-version. Each version has a label, a boolean `is_default` flag (exactly one version is default at all times), and timestamps. Exists as a top-level entity. Can be associated with zero or more applications. The default version serves as the primary resume and as the template for creating new versions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new job application and see it in their list within 5 seconds of submission
- **SC-002**: Users can track an application through the full hiring lifecycle (Interested → Applied → Interview → Offer/Rejected) without leaving the system
- **SC-003**: All data (resumes, applications, contacts, communications) is accessible through all three interfaces (MCP, REST API, UI) with consistent behavior
- **SC-004**: An AI assistant, given access to the MCP tools, can read an application's full context (job description, contacts, communications, default resume) and produce a tailored resume version in a single interaction
- **SC-005**: An AI assistant can draft a contextually relevant follow-up email using the stored job description, contact details, and prior communication history, stored with status "draft"
- **SC-006**: Users can manage 100+ active job applications without noticeable performance degradation in list views
- **SC-007**: Deleting an application cleanly removes all associated contacts and communications with no orphaned records, while preserving shared resume versions
- **SC-008**: Users can create a single resume version and associate it with multiple applications, viewing the association from both the resume version list and each application's detail view
- **SC-009**: Users can progress a communication through the full status workflow (draft → ready → sent → archived) with clear visual indicators at each stage
- **SC-010**: Users can manage multiple resume versions with full editing capabilities on each, and can change which version is the default, with the change reflected immediately across all interfaces

## Clarifications

### Session 2026-02-17

- Q: How should resume versions store data relative to the master resume? → A: Full snapshot — complete copy of all resume fields at creation time, fully independent afterward. Edits to one version do not propagate to other versions.
- Q: Can users add/remove entries in a resume version, or only edit what was copied? → A: Full CRUD — users and AI can add, remove, reorder, and edit any entries within a resume version freely.
- Q: Are application status transitions constrained or free-form? → A: Free-form — any status can transition to any other status with no validation on transitions.
- Q: Should the application list support filtering or search? → A: Filter by status + text search on company name and position title.

### Session 2026-02-17 (rev 2)

- Q: Should communications use a boolean is_draft or a status field? → A: Status field with values: draft, ready, sent, archived. Transitions are free-form.
- Q: Should resume versions be nested under applications or be top-level entities? → A: Top-level entities. One resume version can be shared across many applications. Each application has at most one associated resume version.

### Session 2026-02-17 (rev 3)

- Q: Should the system have a separate "master resume" distinct from resume versions? → A: No. The system manages a list of resume versions, with exactly one marked as default. The default version serves as the primary resume (displayed in the main view, used as the template for new versions). There is no separate master resume API — all resume operations target a specific resume version by ID.
- Q: Should all resume editing capabilities be available on all resume versions? → A: Yes. Every resume version supports full CRUD on all sections (contact, summary, experience, education, skills). There is no distinction between a "master" and a "tailored" version — they are all equal, with one designated as default.

## Assumptions

- The system always has at least one resume version (the default). On first use, the user creates their initial resume version which becomes the default automatically.
- AI-assisted features (resume tuning, communication drafting) rely on the MCP client (e.g., Claude) having the intelligence to produce quality output — the system's responsibility is providing complete context and storing results, not performing the AI reasoning itself.
- Application statuses use a predefined set of values rather than free-text, to enable filtering and consistent tracking. The initial set can be extended in future iterations.
- Communication statuses (draft, ready, sent, archived) are predefined. "sent" is the default for manually logged communications (the user is recording something they already sent). "draft" is the default for AI-generated communications.
- Communications are stored as plain text. Rich formatting (HTML emails) is out of scope for the initial version.
- The web UI follows the same visual patterns and component structure as the existing resume management UI.
- Resume versions are managed in their own top-level list/view in the UI. The "Resumes" view replaces the existing single-resume view and shows all versions with the default prominently indicated.
- The existing single-resume REST API routes (`/api/resume/*`) and MCP tools (`get_resume`, `get_resume_section`, etc.) will be replaced by resume version routes and tools that operate on specific versions by ID. Migration of existing resume data into the first (default) resume version is handled during the database migration.
