# Data Model: Resume Web User Interface

**Branch**: `feat-005-user-interface` | **Date**: 2026-02-12

## Overview

The frontend consumes existing backend data models via the REST API. No new backend entities are introduced. This document maps the existing backend models to their frontend TypeScript counterparts.

## Backend Entities (existing, unchanged)

### ContactInfo
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| name | string | null | No | Personal name |
| email | string | null | No | Email address |
| phone | string | null | No | Phone number |
| location | string | null | No | City/region |
| linkedin | string | null | No | LinkedIn URL |
| website | string | null | No | Personal website URL |
| github | string | null | No | GitHub URL |

### WorkExperience
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | Yes | Job title |
| company | string | Yes | Company name |
| start_date | string | null | No | Free-text date |
| end_date | string | null | No | Free-text date |
| location | string | null | No | Job location |
| highlights | string[] | No | Defaults to [] |

### Education
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| institution | string | Yes | School name |
| degree | string | Yes | Degree type/name |
| field | string | null | No | Field of study |
| start_date | string | null | No | Free-text date |
| end_date | string | null | No | Free-text date |
| honors | string | null | No | Honors/awards |

### Skill
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| name | string | Yes | Skill name (unique) |
| category | string | null | No | Defaults to "Other" |

### Resume (aggregate)
| Field | Type | Default |
|-------|------|---------|
| contact | ContactInfo | empty ContactInfo |
| summary | string | "" |
| experience | WorkExperience[] | [] |
| education | Education[] | [] |
| skills | Skill[] | [] |

## Frontend TypeScript Types

```typescript
// Types mirror the backend Pydantic models exactly.
// Field names use snake_case to match the JSON API responses.

interface ContactInfo {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin: string | null;
  website: string | null;
  github: string | null;
}

interface WorkExperience {
  title: string;
  company: string;
  start_date: string | null;
  end_date: string | null;
  location: string | null;
  highlights: string[];
}

interface Education {
  institution: string;
  degree: string;
  field: string | null;
  start_date: string | null;
  end_date: string | null;
  honors: string | null;
}

interface Skill {
  name: string;
  category: string | null;
}

interface Resume {
  contact: ContactInfo;
  summary: string;
  experience: WorkExperience[];
  education: Education[];
  skills: Skill[];
}
```

## Validation Rules (frontend)

### ContactInfo
- All fields optional (can be null or empty string)
- No format validation enforced on frontend (backend is source of truth)

### WorkExperience
- `title` required, non-empty
- `company` required, non-empty
- `highlights` is an array of strings; empty items should be filtered before submission

### Education
- `institution` required, non-empty
- `degree` required, non-empty

### Skill
- `name` required, non-empty
- `category` optional (defaults to "Other" on backend)

### Summary
- Free text, submitted as `{ text: string }`
- API rejects empty text (422 validation error)

## State Transitions (frontend UI)

Each editable section follows this state machine:

```
[Viewing] → (click edit) → [Editing] → (save) → [Saving] → (success) → [Viewing]
                                      → (cancel) → [Viewing]
                                                   → (error) → [Editing] (with error message)
```

List entries have additional transitions:
```
[Viewing] → (click add) → [Adding] → (save) → [Saving] → (success) → [Viewing]
[Viewing] → (click delete) → [Confirming] → (confirm) → [Deleting] → (success) → [Viewing]
                                           → (cancel) → [Viewing]
```
