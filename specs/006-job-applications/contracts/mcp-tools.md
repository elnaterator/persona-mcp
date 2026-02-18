# MCP Tool Contracts: Job Application Management (rev 3)

**Date**: 2026-02-17
**Feature**: 006-job-applications

## Summary of Tool Changes

The existing 6 MCP tools are **replaced** by new tools. There is no separate "master resume" — all tools operate on resume versions.

### Removed Tools (old)

| Old Name           | Replacement                          |
|--------------------|--------------------------------------|
| `get_resume`       | `get_resume` (now takes optional id) |
| `get_resume_section` | `get_resume_section` (now takes id)|
| `update_section`   | `update_resume_section`              |
| `add_entry`        | `add_resume_entry`                   |
| `update_entry`     | `update_resume_entry`                |
| `remove_entry`     | `remove_resume_entry`                |

## Resume Version Tools

### `list_resumes`

List all resume versions with metadata (no resume content).

**Parameters**: None.

**Returns**: List of resume version summaries (id, label, is_default, app_count, timestamps).

---

### `get_resume`

Get a resume version with full resume data.

**Parameters**:
| Param | Type | Required | Description                              |
|-------|------|----------|------------------------------------------|
| id    | int  | no       | Resume version ID. If omitted, returns the default version. |

**Returns**: Full resume version object including resume_data (contact, summary, experience, education, skills).

**Errors**: Resume version not found.

---

### `get_resume_section`

Get a specific section from a resume version.

**Parameters**:
| Param   | Type   | Required | Description                              |
|---------|--------|----------|------------------------------------------|
| id      | int    | no       | Resume version ID. If omitted, uses default. |
| section | string | yes      | One of: contact, summary, experience, education, skills |

**Returns**: Section data (object for contact, string for summary, array for list sections).

**Errors**: Resume version not found. Invalid section name.

---

### `update_resume_section`

Update a non-list section (contact or summary) on a resume version.

**Parameters**:
| Param   | Type   | Required | Description                              |
|---------|--------|----------|------------------------------------------|
| id      | int    | yes      | Resume version ID                        |
| section | string | yes      | One of: contact, summary                 |
| data    | object | yes      | Fields to update                         |

**Returns**: Success message.

**Errors**: Resume version not found. Invalid section.

---

### `add_resume_entry`

Add an entry to a list section of a resume version.

**Parameters**:
| Param   | Type   | Required | Description                              |
|---------|--------|----------|------------------------------------------|
| id      | int    | yes      | Resume version ID                        |
| section | string | yes      | One of: experience, education, skills    |
| data    | object | yes      | Entry fields                             |

**Returns**: Success message.

---

### `update_resume_entry`

Update an entry in a list section of a resume version.

**Parameters**:
| Param   | Type   | Required | Description                              |
|---------|--------|----------|------------------------------------------|
| id      | int    | yes      | Resume version ID                        |
| section | string | yes      | One of: experience, education, skills    |
| index   | int    | yes      | 0-based index                            |
| data    | object | yes      | Fields to update                         |

**Returns**: Success message.

---

### `remove_resume_entry`

Remove an entry from a list section of a resume version.

**Parameters**:
| Param   | Type   | Required | Description                              |
|---------|--------|----------|------------------------------------------|
| id      | int    | yes      | Resume version ID                        |
| section | string | yes      | One of: experience, education, skills    |
| index   | int    | yes      | 0-based index                            |

**Returns**: Success message.

---

### `create_resume`

Create a new resume version, initialized as a copy of the current default.

**Parameters**:
| Param | Type   | Required | Description        |
|-------|--------|----------|--------------------|
| label | string | yes      | Version label      |

**Returns**: Success message with new version ID.

---

### `set_default_resume`

Set a resume version as the default.

**Parameters**:
| Param | Type | Required | Description       |
|-------|------|----------|-------------------|
| id    | int  | yes      | Resume version ID |

**Returns**: Success message.

**Errors**: Resume version not found. (Already-default is a no-op success.)

---

### `delete_resume`

Delete a resume version.

**Parameters**:
| Param | Type | Required | Description       |
|-------|------|----------|-------------------|
| id    | int  | yes      | Resume version ID |

**Returns**: Success message.

**Errors**: Resume version not found. Cannot delete the last remaining version.

---

## Application Tools

### `list_applications`

List all job applications with optional filtering.

**Parameters**:
| Param  | Type   | Required | Description                          |
|--------|--------|----------|--------------------------------------|
| status | string | no       | Filter by status (exact match)       |
| q      | string | no       | Search company/position (substring)  |

**Returns**: List of application summaries (id, company, position, status, url, resume_version_id, timestamps).

---

### `get_application`

Get full details for a specific application.

**Parameters**:
| Param | Type | Required | Description    |
|-------|------|----------|----------------|
| id    | int  | yes      | Application ID |

**Returns**: Full application object including description and notes.

**Errors**: Application not found.

---

### `create_application`

Create a new job application.

**Parameters**:
| Param             | Type   | Required | Default       | Description              |
|-------------------|--------|----------|---------------|--------------------------|
| company           | string | yes      |               | Company name             |
| position          | string | yes      |               | Position title           |
| description       | string | no       | ""            | Job description text     |
| status            | string | no       | "Interested"  | Initial status           |
| url               | string | no       | null          | Job posting URL          |
| notes             | string | no       | ""            | Free-text notes          |
| resume_version_id | int    | no       | null          | Associated resume version|

**Returns**: Success message with created application ID.

---

### `update_application`

Update an existing application's fields.

**Parameters**:
| Param             | Type   | Required | Description              |
|-------------------|--------|----------|--------------------------|
| id                | int    | yes      | Application ID           |
| company           | string | no       | Updated company name     |
| position          | string | no       | Updated position title   |
| description       | string | no       | Updated job description  |
| status            | string | no       | Updated status           |
| url               | string | no       | Updated URL              |
| notes             | string | no       | Updated notes            |
| resume_version_id | int    | no       | Updated resume version   |

**Returns**: Success message.

---

### `delete_application`

Delete an application and all associated data (cascade).

**Parameters**:
| Param | Type | Required | Description    |
|-------|------|----------|----------------|
| id    | int  | yes      | Application ID |

**Returns**: Success message confirming cascade deletion.

---

### `add_application_contact`

Add a contact to an application.

**Parameters**:
| Param  | Type   | Required | Description         |
|--------|--------|----------|---------------------|
| app_id | int    | yes      | Application ID      |
| name   | string | yes      | Contact's full name |
| role   | string | no       | Role/title          |
| email  | string | no       | Email address       |
| phone  | string | no       | Phone number        |
| notes  | string | no       | Notes about contact |

**Returns**: Success message with contact name.

---

### `update_application_contact`

Update a contact's details.

**Parameters**:
| Param | Type   | Required | Description           |
|-------|--------|----------|-----------------------|
| id    | int    | yes      | Contact ID            |
| name  | string | no       | Updated name          |
| role  | string | no       | Updated role          |
| email | string | no       | Updated email         |
| phone | string | no       | Updated phone         |
| notes | string | no       | Updated notes         |

**Returns**: Success message.

---

### `remove_application_contact`

Remove a contact from an application.

**Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| id    | int  | yes      | Contact ID  |

**Returns**: Success message.

---

### `add_communication`

Log a communication for an application.

**Parameters**:
| Param      | Type   | Required | Default | Description                                    |
|------------|--------|----------|---------|------------------------------------------------|
| app_id     | int    | yes      |         | Application ID                                 |
| type       | string | yes      |         | email, phone, interview_note, other            |
| direction  | string | yes      |         | sent or received                               |
| body       | string | yes      |         | Full content                                   |
| date       | string | yes      |         | ISO 8601 date                                  |
| contact_id | int    | no       | null    | Associated contact ID                          |
| subject    | string | no       | ""      | Subject line                                   |
| status     | string | no       | "sent"  | draft, ready, sent, archived                   |

When `contact_id` is provided, `contact_name` is auto-populated from the referenced contact.

**Status default note**: The default `"sent"` is for manually logged communications (the user is recording something they already sent). AI assistants creating drafts should explicitly pass `status="draft"` per FR-005.

**Returns**: Success message with communication ID.

---

### `update_communication`

Update a communication entry.

**Parameters**:
| Param      | Type   | Required | Description              |
|------------|--------|----------|--------------------------|
| id         | int    | yes      | Communication ID         |
| type       | string | no       | Updated type             |
| direction  | string | no       | Updated direction        |
| subject    | string | no       | Updated subject          |
| body       | string | no       | Updated body             |
| date       | string | no       | Updated date             |
| contact_id | int    | no       | Updated contact ref      |
| status     | string | no       | Updated status           |

**Returns**: Success message.

---

### `remove_communication`

Remove a communication entry.

**Parameters**:
| Param | Type | Required | Description      |
|-------|------|----------|------------------|
| id    | int  | yes      | Communication ID |

**Returns**: Success message.

---

## Composite Context Tool

### `get_application_context`

Get complete context for AI-assisted operations on a specific application.

**Parameters**:
| Param | Type | Required | Description    |
|-------|------|----------|----------------|
| id    | int  | yes      | Application ID |

**Returns**: Object containing:
- `application`: Full application details
- `contacts`: All contacts for this application
- `communications`: All communications (reverse chronological)
- `resume_version`: The application's associated resume version with full data (null if none)
- `default_resume`: The current default resume version with full data

**Errors**: Application not found.
