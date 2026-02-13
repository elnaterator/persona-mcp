# API Contracts: Resume Web User Interface

**Branch**: `feat-005-user-interface` | **Date**: 2026-02-12

## Overview

The frontend consumes the existing REST API. **No new endpoints are introduced.** This document maps frontend user actions to existing API endpoints for reference during implementation.

## Existing Endpoints Used by Frontend

All endpoints are same-origin (no CORS needed). Base path: `/api`.

### Resume Read Operations

#### Get Full Resume
```
GET /api/resume → 200 OK
```
**Frontend usage**: Initial page load — fetch all resume data at once.

**Response**: `Resume` object (contact, summary, experience[], education[], skills[])

---

#### Get Single Section
```
GET /api/resume/{section} → 200 OK | 404 Not Found
```
**Frontend usage**: Refresh a single section after edit (optional optimization).

**Path params**: `section` ∈ {contact, summary, experience, education, skills}

---

### Contact & Summary Updates

#### Update Contact
```
PUT /api/resume/contact → 200 OK | 422 Validation Error
```
**Frontend usage**: Save contact form.

**Request body**: Partial `ContactInfo` (only include changed fields).

**Response**: `{ "message": "Updated contact fields: name, email" }`

---

#### Update Summary
```
PUT /api/resume/summary → 200 OK | 422 Validation Error
```
**Frontend usage**: Save summary text.

**Request body**: `{ "text": "New summary text" }` (text must be non-empty)

**Response**: `{ "message": "Updated summary" }`

---

### List Entry Operations

#### Add Entry
```
POST /api/resume/{section}/entries → 201 Created | 400 Bad Request | 422 Validation Error
```
**Frontend usage**: Add new experience, education, or skill.

**Path params**: `section` ∈ {experience, education, skills}

**Request body**: Full entry object (required fields must be present).

**Response**: `{ "message": "Added experience entry: Title at Company" }`

---

#### Update Entry
```
PUT /api/resume/{section}/entries/{index} → 200 OK | 404 Not Found | 422 Validation Error
```
**Frontend usage**: Edit an existing entry.

**Path params**: `section` ∈ {experience, education, skills}, `index` ∈ 0..N-1

**Request body**: Partial entry (only include changed fields).

**Response**: `{ "message": "Updated experience entry at index 0: Title at Company" }`

---

#### Remove Entry
```
DELETE /api/resume/{section}/entries/{index} → 200 OK | 404 Not Found
```
**Frontend usage**: Delete an entry after user confirmation.

**Path params**: `section` ∈ {experience, education, skills}, `index` ∈ 0..N-1

**Response**: `{ "message": "Removed experience entry: Title at Company" }`

---

### Health Check

#### Health
```
GET /health → 200 OK
```
**Frontend usage**: Not directly used by UI, but available for container orchestration.

---

## Error Response Format

All error responses follow this pattern:

```json
{
  "detail": "Human-readable error message"
}
```

**Status codes the frontend must handle**:
- `200` / `201`: Success
- `400`: Invalid section for operation
- `404`: Section not found or entry index out of range
- `422`: Validation error (missing required fields, empty text)
- `5xx`: Server error (network issues, database problems)

## New Backend Change: Static File Serving

The only backend change is adding static file serving for the frontend assets:

- **Mount**: `StaticFiles` at `/` pointing to the frontend build output directory
- **Behavior**: Serves `index.html` for `/` and static assets (JS, CSS, images)
- **Priority**: API routes (`/api/*`), MCP (`/mcp`), and health (`/health`) take precedence
- **Fallback**: If frontend assets directory doesn't exist, the mount is skipped (backend starts normally)
