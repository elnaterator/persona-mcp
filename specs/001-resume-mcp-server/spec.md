# Feature Specification: Personal MCP Server with Resume Tools

**Feature Branch**: `001-resume-mcp-server`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "Create an MCP server that can fetch personal information for the purpose of helping with job searches, updating resumes, given that the data source is a folder within 1 or more external data source repositories. The data source repos should be configurable with environment variables, and there should be an expected, prescribed directory structure that the MCP server will use or create in those repos. It should sync those repos on startup to ensure latest changes, and commit changes to those repos periodically as it makes updates to the contents. The first set of tools is around maintaining a resume, but keep in mind that features will expand in the future."

## Clarifications

### Session 2026-02-07

- Q: What file format for resume data? → A: Single Markdown file with YAML front-matter for contact fields, Markdown body with `##` headings for sections.
- Q: What directory structure layout? → A: `job-search/resume/resume.md` under the data root. Future features get sibling directories under `job-search/`.
- Q: Which fields in front-matter vs. body? → A: Front-matter: contact info (name, email, phone, location, LinkedIn, website, GitHub). Body: `## Summary`, `## Experience`, `## Education`, `## Skills`.
- Q: Git integration approach? → A: No git integration. The server points to a single local directory (default `~/.personal-mcp/`, overridable via environment variable). Whether that directory is a git repo is the user's concern.
- Q: Logging & observability? → A: Python `logging` to stderr, INFO level by default, configurable via `LOG_LEVEL` environment variable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Resume Data (Priority: P1)

A user starts the MCP server (optionally overriding the data directory via environment variable). An AI assistant connected via MCP can retrieve the user's current resume information — contact details, work experience, education, skills, and summary — from the `job-search/resume/resume.md` file in the data directory. The user can ask questions like "What is my current job title?" or "List my skills" and get accurate answers drawn from their personal data.

**Why this priority**: This is the foundational read path. Without the ability to read personal data, no other feature (editing, searching) has value. This story alone delivers a useful MCP server that can answer resume-related questions.

**Independent Test**: Can be fully tested by placing a sample `resume.md` in the data directory's `job-search/resume/` path, starting the server, and issuing MCP tool calls to retrieve resume sections.

**Acceptance Scenarios**:

1. **Given** the data directory contains `job-search/resume/resume.md` with valid content, **When** the server starts, **Then** it can serve resume data through MCP tool calls without errors.
2. **Given** the data directory exists but has no `job-search/resume/` path yet, **When** the server starts, **Then** it creates the directory structure automatically.
3. **Given** the `PERSONAL_MCP_DATA_DIR` environment variable is not set, **When** the server starts, **Then** it uses `~/.personal-mcp/` as the data directory.
4. **Given** the environment variable points to a non-existent path, **When** the server starts, **Then** it creates the directory (and subdirectories) automatically.

---

### User Story 2 - Update Resume Data (Priority: P2)

A user asks their AI assistant to update their resume — for example, adding a new job, updating skills, or editing their summary. The MCP server writes these changes to `job-search/resume/resume.md` in the data directory. The changes are persisted so they survive server restarts.

**Why this priority**: After being able to read data, the natural next step is editing it. This completes the read-write loop and makes the server a practical tool for maintaining a living resume rather than a read-only reference.

**Independent Test**: Can be tested by issuing MCP tool calls to update a resume field (e.g., add a skill), then reading back the data to confirm the change persisted.

**Acceptance Scenarios**:

1. **Given** the server is running with a writable data directory, **When** a tool call requests adding a new work experience entry, **Then** the entry is written to `resume.md` and can be read back immediately.
2. **Given** the server is running, **When** a tool call requests updating an existing field (e.g., job title), **Then** the field is updated in place without corrupting other data.
3. **Given** the server is running, **When** a tool call requests removing a skill, **Then** the skill is removed from the data and the change persists.

---

### Edge Cases

- What happens when the data directory path is a relative path instead of absolute?
  The server MUST resolve relative paths against the current working directory and log the resolved absolute path.
- What happens when `resume.md` exists but is malformed (invalid front-matter or unparseable Markdown)?
  The server MUST report the parsing error as a warning via logging and return empty/default values for affected sections without crashing.
- What happens when `resume.md` is empty?
  The server MUST treat it as absent data (return empty/default values for all sections).
- What happens when the server loses write access to the data directory mid-session?
  Write operations MUST fail gracefully with a clear error message; read operations MUST continue unaffected.
- What happens when the data directory does not exist and cannot be created (e.g., permissions)?
  The server MUST report a clear error at startup identifying the path and the permission issue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use a single local directory as the data root, defaulting to `~/.personal-mcp/` and overridable via `PERSONAL_MCP_DATA_DIR` environment variable.
- **FR-002**: System MUST use the directory structure `job-search/resume/resume.md` under the data root for resume data. Future features will use sibling directories under `job-search/`.
- **FR-003**: System MUST create the directory structure and an empty `resume.md` file if they do not already exist on startup.
- **FR-004**: System MUST expose MCP tools to read individual resume sections (experience, education, skills, contact info, summary) from the single `resume.md` file.
- **FR-005**: System MUST expose MCP tools to add, update, and remove entries within each resume section.
- **FR-006**: System MUST store resume data as a single Markdown file with YAML front-matter (contact info) and `##`-headed body sections (Summary, Experience, Education, Skills).
- **FR-007**: System MUST resolve relative data directory paths against the current working directory.
- **FR-008**: System MUST log operations to stderr using Python `logging` at INFO level by default, configurable via `LOG_LEVEL` environment variable.

### Key Entities

- **Data Directory**: A local filesystem directory containing personal data. Defaults to `~/.personal-mcp/`, overridable via `PERSONAL_MCP_DATA_DIR`.
- **Resume** (`job-search/resume/resume.md`): A single Markdown file with YAML front-matter (contact info) and body sections. Composed of: Contact Info (front-matter), Summary, Work Experience, Education, and Skills (body `##` sections).
- **Work Experience Entry**: A single job or role held. Attributes: company name, job title, start date, end date (or "present"), location, description/bullet points.
- **Education Entry**: A single educational credential. Attributes: institution name, degree, field of study, start date, end date, honors or notes.
- **Skill**: A named competency or technology. Attributes: name, optional category (e.g., "Programming Languages", "Frameworks", "Soft Skills").
- **Contact Info** (YAML front-matter): Personal contact details. Attributes: full name, email, phone, location, LinkedIn URL, personal website, GitHub profile.
- **Summary**: A brief professional summary or objective statement. Attributes: text content.

### Assumptions

- The data directory is a local filesystem path. The server has no awareness of git or version control — versioning is the user's responsibility.
- The server runs as a single-user, local process. There are no multi-user or authentication concerns.
- The resume file format is Markdown with YAML front-matter, human-readable and editable outside the MCP server.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can retrieve any section of their resume data within 2 seconds of issuing the request, given a resume file with up to 50 entries across all sections.
- **SC-002**: A user can add, update, or remove a resume entry and read back the change immediately (within the same session) with 100% consistency.
- **SC-003**: The server starts and is ready to serve requests within 2 seconds.
- **SC-004**: The server starts successfully and creates the directory structure and empty `resume.md` when the data directory has no existing `job-search/resume/` path.
- **SC-005**: The `resume.md` file format is documented clearly enough that a user can manually create or edit the resume without using the MCP server.
