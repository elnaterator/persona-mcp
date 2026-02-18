# Research: Job Application Management (rev 3)

**Date**: 2026-02-17
**Feature**: 006-job-applications

## Decision 1: Resume Version Storage Model

**Decision**: Resume versions store data as a JSON blob in a single `resume_data TEXT` column, containing the full Resume structure (contact, summary, experience, education, skills).

**Rationale**: The existing codebase stores resume data across 5 separate tables (contact, summary, experience, education, skill) with a singleton pattern (id=1). For resume versions, we need multiple independent copies. A JSON blob avoids duplicating 5 tables with a version_id FK and keeps each version self-contained. The Resume Pydantic model provides serialization/deserialization. Section-level editing is handled by deserializing the blob, mutating the section in Python, and writing the blob back.

**Alternatives considered**:
- Parallel versioned tables (contact_v, summary_v, experience_v, etc.): More complex schema, many FKs, harder migration. Offers SQL-level querying of individual fields but this isn't needed — we never query "all resumes with skill X."
- Separate JSON columns per section: Adds complexity without meaningful benefit over a single blob.

## Decision 2: Migration from Singleton Resume to Default Resume Version

**Decision**: Migration v1→v2 creates a `resume_version` table, migrates existing data from the 5 singleton tables into the first resume version (id=1, is_default=1, label="Default Resume"), and drops the old singleton tables (contact, summary, experience, education, skill).

**Rationale**: The spec says "there is no separate master resume — the system maintains a list of resume versions." The cleanest migration path is to snapshot the existing data into the first version, then remove the old tables. This preserves all user data while making a clean break.

**Alternatives considered**:
- Keep old tables as a "special" default: Creates two code paths forever. Rejected.
- Keep old tables for backward compatibility: Adds confusion and maintenance burden.

## Decision 3: MCP Tool Naming for Resume Versions

**Decision**: The existing 6 MCP tools are replaced with 10 new tools that add version awareness:
- `list_resumes` — list all resume versions with metadata
- `get_resume` — get a specific resume version by ID (omit ID to get default)
- `get_resume_section` — get a section from a specific version
- `update_resume_section` — update contact/summary on a version
- `add_resume_entry` — add entry to a version's list section
- `update_resume_entry` — update entry in a version
- `remove_resume_entry` — remove entry from a version
- `create_resume` — create a new resume version from default
- `set_default_resume` — change which version is default
- `delete_resume` — delete a resume version

**Rationale**: Keeps existing tool semantics (section-level operations) while adding version awareness. The optional `id` on `get_resume` preserves backward-compatible AI workflows ("get my resume" still works by returning the default).

**Alternatives considered**:
- Whole-resume replacement tools only: Too coarse for AI assistants that want to edit a single section.
- Keep old tool names plus new ones: Creates confusion about which tools to use.

## Decision 4: REST API Route Structure

**Decision**: Replace existing `/api/resume/*` routes with `/api/resumes/*` routes. Application routes under `/api/applications/*`. Resume section editing nested under version ID.

**Rationale**: RESTful plural noun with ID-based access is standard. Section editing routes nest naturally under the version. A `/api/resumes/default` convenience alias supports the common case.

**Alternatives considered**:
- Keep `/api/resume` (singular) as alias: Creates ambiguity between old and new API.
- Single endpoint with action params: Not RESTful.

## Decision 5: Frontend Navigation Architecture

**Decision**: State-based navigation with a top-level nav component. Three main views: Resumes, Applications, and detail views for each. No React Router.

**Rationale**: The existing app is a single-component app. State-based navigation avoids a new dependency and is consistent with the constitution's minimal-dependencies principle.

**Alternatives considered**:
- React Router: Adds dependency unnecessarily for a personal tool.
- Tab-based UI: Doesn't support detail views well.

## Decision 6: UI Resume Version Management

**Decision**: The "Resumes" view replaces the existing single ResumeView. It shows a list of resume versions with labels, default indicator, and application count. Clicking a version opens the same section-editing UI (ContactSection, SummarySection, etc.) scoped to that version.

**Rationale**: Reuses existing section components with minimal changes — they just need to call version-scoped API endpoints.

**Alternatives considered**:
- Side-by-side comparison view: Scope creep for v1.

## Decision 7: Application Context Tool

**Decision**: The `get_application_context` MCP tool returns both the application's associated resume version (if any) and the default resume.

**Rationale**: AI assistants need the default resume to create tailored versions and the associated version to see what was used for this application.

**Alternatives considered**:
- Only return associated or only default: Missing context in different scenarios.
