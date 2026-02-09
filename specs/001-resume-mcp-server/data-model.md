# Data Model: Persona MCP Server with Resume Tools

**Date**: 2026-02-09
**Feature**: 001-resume-mcp-server
**Source**: [spec.md](spec.md) Key Entities + [research.md](research.md)

## Overview

The resume data lives in a single Markdown file (`jobs/resume/resume.md`) under the persona data directory. The file uses YAML front-matter for contact information and Markdown `##` sections for the resume body. Pydantic models provide the in-memory representation with validation.

## File Format

```markdown
---
name: "Jane Doe"
email: "jane@example.com"
phone: "+1-555-0100"
location: "San Francisco, CA"
linkedin: "https://linkedin.com/in/janedoe"
website: "https://janedoe.dev"
github: "https://github.com/janedoe"
---

## Summary

Experienced software engineer with 10 years...

## Experience

### Senior Software Engineer | Acme Corp
- **Start**: 2021-01
- **End**: present
- **Location**: San Francisco, CA

- Led migration of monolithic application to microservices
- Reduced deployment time by 60%

### Software Engineer | StartupCo
- **Start**: 2018-06
- **End**: 2020-12
- **Location**: New York, NY

- Built real-time data pipeline processing 1M events/day
- Mentored 3 junior engineers

## Education

### M.S. Computer Science | Stanford University
- **Start**: 2016-09
- **End**: 2018-05
- **Honors**: Dean's List

### B.S. Computer Science | UC Berkeley
- **Start**: 2012-09
- **End**: 2016-05

## Skills

### Programming Languages
- Python
- TypeScript
- Go

### Frameworks
- FastAPI
- React
- Kubernetes

### Soft Skills
- Technical Leadership
- Mentoring
```

## Entities

### ContactInfo

Stored in YAML front-matter. All fields are optional strings.

| Field    | Type         | Description                    | Required |
|----------|--------------|--------------------------------|----------|
| name     | string       | Full name                      | No       |
| email    | string       | Email address                  | No       |
| phone    | string       | Phone number                   | No       |
| location | string       | City, state/country            | No       |
| linkedin | string       | LinkedIn profile URL           | No       |
| website  | string       | Personal website URL           | No       |
| github   | string       | GitHub profile URL             | No       |

### WorkExperience

Stored as `### Title | Company` subsections under `## Experience`.

| Field       | Type         | Description                          | Required |
|-------------|--------------|--------------------------------------|----------|
| title       | string       | Job title                            | Yes      |
| company     | string       | Company name                         | Yes      |
| start_date  | string       | Start date (YYYY-MM format)          | No       |
| end_date    | string       | End date or "present"                | No       |
| location    | string       | Work location                        | No       |
| highlights  | list[string] | Bullet-point achievements            | No       |

### Education

Stored as `### Degree | Institution` subsections under `## Education`.

| Field       | Type         | Description                          | Required |
|-------------|--------------|--------------------------------------|----------|
| institution | string       | School or university name            | Yes      |
| degree      | string       | Degree name                          | Yes      |
| field       | string       | Field of study (part of degree)      | No       |
| start_date  | string       | Start date (YYYY-MM format)          | No       |
| end_date    | string       | End date (YYYY-MM format)            | No       |
| honors      | string       | Honors, GPA, or notes                | No       |

### Skill

Stored as categorized lists under `## Skills`. Each `### Category` subsection contains a bullet list of skill names.

| Field    | Type         | Description                          | Required |
|----------|--------------|--------------------------------------|----------|
| name     | string       | Skill name                           | Yes      |
| category | string       | Grouping category                    | No       |

### Resume (Aggregate)

The top-level entity combining all sections.

| Field       | Type                | Description               |
|-------------|---------------------|---------------------------|
| contact     | ContactInfo         | YAML front-matter fields  |
| summary     | string              | Professional summary text |
| experience  | list[WorkExperience]| Work history entries      |
| education   | list[Education]     | Education entries         |
| skills      | list[Skill]         | Skills with categories    |

## Relationships

```
Resume (1)
├── ContactInfo (1)
├── Summary (1)
├── WorkExperience (0..N)
├── Education (0..N)
└── Skill (0..N, grouped by category)
```

## Validation Rules

1. **ContactInfo**: All fields optional. No format validation beyond string type (URLs, emails, and phone numbers are stored as-is since they come from the user).
2. **WorkExperience**: `title` and `company` are required. If `end_date` is absent, the role is assumed to be current.
3. **Education**: `institution` and `degree` are required.
4. **Skill**: `name` is required. If no `category` is provided, the skill is placed under an "Other" category.
5. **Resume**: All sections default to empty (empty contact, empty string summary, empty lists) when `resume.md` is absent or empty.

## State Transitions

Resume data is stateless — there are no workflow states. The file is read on each tool call and written immediately on each mutation. There is no caching or in-memory state between tool calls.
