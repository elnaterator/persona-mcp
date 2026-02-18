# REST API Contracts: Job Application Management (rev 3)

**Date**: 2026-02-17
**Feature**: 006-job-applications

## Summary of Route Changes

The existing `/api/resume/*` routes are **replaced** by `/api/resumes/*` routes that operate on resume versions by ID. The old singleton resume concept is eliminated.

### Removed Routes (old)

```
GET    /api/resume
GET    /api/resume/{section}
PUT    /api/resume/contact
PUT    /api/resume/summary
POST   /api/resume/{section}/entries
PUT    /api/resume/{section}/entries/{index}
DELETE /api/resume/{section}/entries/{index}
```

### New Routes

```
# Resume Versions
GET    /api/resumes                                        → list versions
POST   /api/resumes                                        → create version
GET    /api/resumes/default                                → get default version
GET    /api/resumes/{id}                                   → get version
PUT    /api/resumes/{id}                                   → update version metadata
DELETE /api/resumes/{id}                                   → delete version
PUT    /api/resumes/{id}/default                           → set as default
GET    /api/resumes/{id}/{section}                         → get section
PUT    /api/resumes/{id}/contact                           → update contact
PUT    /api/resumes/{id}/summary                           → update summary
POST   /api/resumes/{id}/{section}/entries                 → add entry
PUT    /api/resumes/{id}/{section}/entries/{index}         → update entry
DELETE /api/resumes/{id}/{section}/entries/{index}         → remove entry

# Applications
GET    /api/applications                                   → list applications
POST   /api/applications                                   → create application
GET    /api/applications/{id}                              → get application
PUT    /api/applications/{id}                              → update application
DELETE /api/applications/{id}                              → delete application (cascade)

# Application Contacts
GET    /api/applications/{id}/contacts                     → list contacts
POST   /api/applications/{id}/contacts                     → add contact
PUT    /api/applications/{id}/contacts/{contact_id}        → update contact
DELETE /api/applications/{id}/contacts/{contact_id}        → remove contact

# Communications
GET    /api/applications/{id}/communications               → list communications
POST   /api/applications/{id}/communications               → add communication
PUT    /api/applications/{id}/communications/{comm_id}     → update communication
DELETE /api/applications/{id}/communications/{comm_id}     → remove communication

# Application Context (AI composite)
GET    /api/applications/{id}/context                      → full context for AI
```

---

## Resume Version Routes

### `GET /api/resumes`

List all resume versions with metadata (no resume_data).

**Response** `200`:
```json
[
  {
    "id": 1,
    "label": "Default Resume",
    "is_default": true,
    "app_count": 3,
    "created_at": "2026-02-17T10:00:00Z",
    "updated_at": "2026-02-17T12:00:00Z"
  }
]
```

---

### `POST /api/resumes`

Create a new resume version, initialized as a copy of the current default resume.

**Request Body**:
```json
{
  "label": "Technical Focus"
}
```

Required: `label`.

**Response** `201`: Full resume version object including `resume_data`.

**Errors**: `422` if label empty. `404` if no default resume exists (shouldn't happen — system invariant).

---

### `GET /api/resumes/default`

Convenience alias: returns the default resume version with full `resume_data`.

**Response** `200`: Same shape as `GET /api/resumes/{id}`.

**Errors**: `404` if no default exists.

---

### `GET /api/resumes/{id}`

Get a resume version with full resume data.

**Response** `200`:
```json
{
  "id": 1,
  "label": "Default Resume",
  "is_default": true,
  "resume_data": {
    "contact": { "name": "...", "email": "...", ... },
    "summary": "...",
    "experience": [ ... ],
    "education": [ ... ],
    "skills": [ ... ]
  },
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T12:00:00Z"
}
```

**Errors**: `404` if not found.

---

### `PUT /api/resumes/{id}`

Update resume version metadata (label only). Use section-specific routes for resume content.

**Request Body**: `{"label": "New Label"}`

**Response** `200`: Updated resume version object (full).

**Errors**: `404` if not found, `422` if validation fails.

---

### `DELETE /api/resumes/{id}`

Delete a resume version. Removes association from all linked applications.

**Response** `200`:
```json
{
  "message": "Deleted resume version 'Technical Focus'"
}
```

**Errors**: `404` if not found. `409` if it's the only version (cannot delete last remaining version).

---

### `PUT /api/resumes/{id}/default`

Set this resume version as the default.

**Request Body**: None required.

**Response** `200`:
```json
{
  "message": "Set 'Technical Focus' as default resume"
}
```

**Errors**: `404` if not found. (Setting already-default version is a no-op success.)

---

### `GET /api/resumes/{id}/{section}`

Get a specific section of a resume version.

**Path Parameters**: `section` is one of: `contact`, `summary`, `experience`, `education`, `skills`.

**Response** `200`: Section data (object for contact, string for summary, array for list sections).

**Errors**: `404` if version or section not found.

---

### `PUT /api/resumes/{id}/contact`

Update contact info on a resume version (partial merge).

**Request Body**: Any subset of contact fields.

**Response** `200`: `{"message": "Updated contact fields: name, email"}`

**Errors**: `404` if not found, `422` if validation fails.

---

### `PUT /api/resumes/{id}/summary`

Update summary text on a resume version.

**Request Body**: `{"text": "New summary..."}`

**Response** `200`: `{"message": "Updated summary"}`

**Errors**: `404` if not found, `422` if empty text.

---

### `POST /api/resumes/{id}/{section}/entries`

Add an entry to a list section of a resume version.

**Path Parameters**: `section` is one of: `experience`, `education`, `skills`.

**Request Body**: Entry data (fields vary by section).

**Response** `201`: `{"message": "Added experience entry: ..."}`

**Errors**: `404` if not found, `422` if validation fails.

---

### `PUT /api/resumes/{id}/{section}/entries/{index}`

Update an entry in a list section by index.

**Response** `200`: `{"message": "Updated experience entry at index 0: ..."}`

**Errors**: `404` if version not found or index out of range, `422` if validation fails.

---

### `DELETE /api/resumes/{id}/{section}/entries/{index}`

Remove an entry from a list section by index.

**Response** `200`: `{"message": "Removed experience entry: ..."}`

**Errors**: `404` if version not found or index out of range.

---

## Application Routes

### `GET /api/applications`

List applications with optional filtering.

**Query Parameters**:
| Param  | Type   | Required | Description                                  |
|--------|--------|----------|----------------------------------------------|
| status | string | no       | Filter by status (exact match)               |
| q      | string | no       | Search company name and position title (case-insensitive substring) |

**Response** `200`:
```json
[
  {
    "id": 1,
    "company": "Acme Corp",
    "position": "Senior Engineer",
    "status": "Applied",
    "url": "https://example.com/job/123",
    "resume_version_id": 2,
    "created_at": "2026-02-17T10:00:00Z",
    "updated_at": "2026-02-17T12:00:00Z"
  }
]
```

Note: List response omits `description` and `notes` for brevity.

---

### `POST /api/applications`

Create a new application.

**Request Body**:
```json
{
  "company": "Acme Corp",
  "position": "Senior Engineer",
  "description": "We are looking for...",
  "status": "Interested",
  "url": "https://example.com/job/123",
  "notes": "",
  "resume_version_id": null
}
```

Required: `company`, `position`. Optional: `description`, `status` (default: "Interested"), `url`, `notes`, `resume_version_id`.

**Response** `201`: Full application object.

**Errors**: `422` if validation fails.

---

### `GET /api/applications/{id}`

Get full application details.

**Response** `200`:
```json
{
  "id": 1,
  "company": "Acme Corp",
  "position": "Senior Engineer",
  "description": "We are looking for...",
  "status": "Applied",
  "url": "https://example.com/job/123",
  "notes": "Referred by Jane",
  "resume_version_id": 2,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T12:00:00Z"
}
```

**Errors**: `404` if not found.

---

### `PUT /api/applications/{id}`

Update application fields (partial update).

**Request Body**: Any subset of `company`, `position`, `description`, `status`, `url`, `notes`, `resume_version_id`.

**Response** `200`: Updated application object.

**Errors**: `404` if not found, `422` if validation fails.

---

### `DELETE /api/applications/{id}`

Delete application and all associated data (cascade).

**Response** `200`:
```json
{
  "message": "Deleted application 'Senior Engineer at Acme Corp' and all associated data"
}
```

**Errors**: `404` if not found.

---

## Application Contact Routes

### `GET /api/applications/{id}/contacts`

**Response** `200`:
```json
[
  {
    "id": 7,
    "app_id": 1,
    "name": "Jane Smith",
    "role": "Recruiter",
    "email": "jane@acme.com",
    "phone": "555-1234",
    "notes": ""
  }
]
```

**Errors**: `404` if application not found.

---

### `POST /api/applications/{id}/contacts`

**Request Body**:
```json
{
  "name": "Jane Smith",
  "role": "Recruiter",
  "email": "jane@acme.com",
  "phone": "555-1234",
  "notes": ""
}
```

Required: `name`. Optional: `role`, `email`, `phone`, `notes`.

**Response** `201`: Created contact object.

**Errors**: `404` if application not found, `422` if validation fails.

---

### `PUT /api/applications/{id}/contacts/{contact_id}`

Partial update of contact.

**Response** `200`: Updated contact object.

**Errors**: `404` if not found, `422` if validation fails.

---

### `DELETE /api/applications/{id}/contacts/{contact_id}`

Remove a contact. Communications referencing this contact have `contact_id` set to null.

**Response** `200`: `{"message": "Removed contact 'Jane Smith'"}`

**Errors**: `404` if not found.

---

## Communication Routes

### `GET /api/applications/{id}/communications`

List communications, ordered by date descending.

**Response** `200`:
```json
[
  {
    "id": 12,
    "app_id": 1,
    "contact_id": 7,
    "contact_name": "Jane Smith",
    "type": "email",
    "direction": "sent",
    "subject": "Following up on interview",
    "body": "Hi Jane, ...",
    "date": "2026-02-15",
    "status": "sent",
    "created_at": "2026-02-15T14:00:00Z"
  }
]
```

**Errors**: `404` if application not found.

---

### `POST /api/applications/{id}/communications`

**Request Body**:
```json
{
  "contact_id": 7,
  "type": "email",
  "direction": "sent",
  "subject": "Following up on interview",
  "body": "Hi Jane, ...",
  "date": "2026-02-15",
  "status": "sent"
}
```

Required: `type`, `direction`, `body`, `date`. Optional: `contact_id`, `subject`, `status` (default: "sent"). When `contact_id` is provided, `contact_name` is auto-populated.

**Response** `201`: Created communication object.

**Errors**: `404` if application not found, `422` if validation fails.

---

### `PUT /api/applications/{id}/communications/{comm_id}`

Partial update.

**Response** `200`: Updated communication object.

**Errors**: `404` if not found, `422` if validation fails.

---

### `DELETE /api/applications/{id}/communications/{comm_id}`

**Response** `200`: `{"message": "Removed communication 'Following up on interview'"}`

**Errors**: `404` if not found.

---

## Application Context (AI Composite)

### `GET /api/applications/{id}/context`

Get full context for AI-assisted operations.

**Response** `200`:
```json
{
  "application": { ... },
  "contacts": [ ... ],
  "communications": [ ... ],
  "resume_version": { ... },
  "default_resume": { ... }
}
```

- `resume_version`: The application's associated resume version (null if none)
- `default_resume`: The current default resume version (always present)

**Errors**: `404` if application not found.
