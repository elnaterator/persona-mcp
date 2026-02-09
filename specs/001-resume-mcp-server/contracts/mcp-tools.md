# MCP Tool Contracts: Persona Resume Tools

**Date**: 2026-02-09
**Feature**: 001-resume-mcp-server

## Overview

All tools are exposed via the MCP protocol over STDIO transport. Tool inputs and outputs use JSON. Errors are returned as MCP error responses with human-readable messages (no stack traces).

The tool surface uses a **generic section-based design**: instead of per-entity tools (e.g., `add_experience`, `add_education`), a small set of generic CRUD tools accept a `section` parameter and a `data` dict whose valid fields depend on the section. Validation is dispatched internally to per-section Pydantic models.

### Supported Sections

| Section      | List-based | Data fields                                                        |
|--------------|------------|--------------------------------------------------------------------|
| `contact`    | No         | name, email, phone, location, linkedin, website, github            |
| `summary`    | No         | text (string)                                                      |
| `experience` | Yes        | title*, company*, start_date, end_date, location, highlights       |
| `education`  | Yes        | institution*, degree*, field, start_date, end_date, honors         |
| `skills`     | Yes        | name*, category                                                    |

\* = required field

---

## P1 Tools (Read)

### `get_resume`

Retrieves the full resume as structured data.

**Input Schema**: (no parameters)

```json
{}
```

**Output Schema**:

```json
{
  "contact": {
    "name": "string | null",
    "email": "string | null",
    "phone": "string | null",
    "location": "string | null",
    "linkedin": "string | null",
    "website": "string | null",
    "github": "string | null"
  },
  "summary": "string",
  "experience": [
    {
      "title": "string",
      "company": "string",
      "start_date": "string | null",
      "end_date": "string | null",
      "location": "string | null",
      "highlights": ["string"]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "start_date": "string | null",
      "end_date": "string | null",
      "honors": "string | null"
    }
  ],
  "skills": [
    {
      "name": "string",
      "category": "string"
    }
  ]
}
```

**Error cases**:
- Data directory unreadable → error message with path and permission details
- `resume.md` malformed → warning logged, empty/default values returned (not an error to the caller)
- `resume.md` absent or empty → empty resume returned (all fields empty/default)

---

### `get_resume_section`

Retrieves a single resume section by name.

**Input Schema**:

```json
{
  "section": "string (enum: contact, summary, experience, education, skills)"
}
```

**Output Schema**: The corresponding section object from the `get_resume` output. Examples:
- `section: "contact"` → `{ "name": "...", "email": "...", ... }`
- `section: "experience"` → `[ { "title": "...", ... }, ... ]`
- `section: "summary"` → `"string"`
- `section: "skills"` → `[ { "name": "...", "category": "..." }, ... ]`

**Error cases**:
- Invalid section name → error: "Invalid section: '{name}'. Must be one of: contact, summary, experience, education, skills"

---

## P2 Tools (Write)

### `update_section`

Updates a non-list section (contact or summary). For `contact`, only provided fields are updated; omitted fields are left unchanged. For `summary`, the text is replaced entirely.

**Input Schema**:

```json
{
  "section": "string (enum: contact, summary)",
  "data": "object"
}
```

**`data` by section**:

- `contact`: `{ "name": "...", "email": "...", ... }` — any subset of contact fields
- `summary`: `{ "text": "string" }`

**Output**: Confirmation message listing what was updated.

**Error cases**:
- Invalid section → error: "Invalid section for update_section: '{name}'. Must be one of: contact, summary"
- `contact` with no fields → error: "At least one contact field must be provided"
- `summary` with empty text → error: "Summary text must not be empty"
- Write failure → error with path and permission details

---

### `add_entry`

Adds a new entry to a list-based section. New entries are prepended (most recent first).

**Input Schema**:

```json
{
  "section": "string (enum: experience, education, skills)",
  "data": "object"
}
```

**`data` by section**:

- `experience`: `{ "title": "string", "company": "string", "start_date": "string?", "end_date": "string?", "location": "string?", "highlights": ["string"]? }`
- `education`: `{ "institution": "string", "degree": "string", "field": "string?", "start_date": "string?", "end_date": "string?", "honors": "string?" }`
- `skills`: `{ "name": "string", "category": "string?" }` — category defaults to "Other" if omitted or null

**Output**: Confirmation message with added entry summary.

**Error cases**:
- Invalid section → error: "Invalid section for add_entry: '{name}'. Must be one of: experience, education, skills"
- Missing required fields → validation error listing which fields are required for the section
- Duplicate skill name (case-insensitive) → error: "Skill '{name}' already exists under category '{category}'"
- Write failure → error with path and permission details

---

### `update_entry`

Updates an existing entry in a list-based section, identified by index (0-based, ordered as they appear in the file). Only provided fields are updated; omitted fields are left unchanged.

**Input Schema**:

```json
{
  "section": "string (enum: experience, education, skills)",
  "index": "integer (0-based)",
  "data": "object"
}
```

**`data` by section**: Same fields as `add_entry`, but all fields are optional (partial update). For skills: setting `category` to null or empty string reverts it to "Other".

**Output**: Confirmation message with updated entry summary.

**Error cases**:
- Invalid section → error: "Invalid section for update_entry: '{name}'. Must be one of: experience, education, skills"
- Index out of range → error: "{Section} index {index} out of range. Resume has {count} {section} entries."
- No fields provided in data → error: "At least one field must be provided to update"
- Write failure → error with path and permission details

---

### `remove_entry`

Removes an entry from a list-based section by index.

**Input Schema**:

```json
{
  "section": "string (enum: experience, education, skills)",
  "index": "integer (0-based)"
}
```

**Output**: Confirmation message with removed entry summary.

**Error cases**:
- Invalid section → error: "Invalid section for remove_entry: '{name}'. Must be one of: experience, education, skills"
- Index out of range → error: "{Section} index {index} out of range. Resume has {count} {section} entries."
- Write failure → error with path and permission details
