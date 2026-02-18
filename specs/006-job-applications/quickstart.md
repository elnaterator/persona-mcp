# Quickstart: Job Application Management (rev 3)

**Date**: 2026-02-17
**Feature**: 006-job-applications

## Prerequisites

- Python 3.11+ with `uv`
- Node.js 18+ with `npm`
- Existing persona project with resume data (will be migrated)

## Quick Verification Scenarios

### 1. Resume Version Management

```bash
# List resume versions (should show migrated default)
curl http://localhost:8080/api/resumes

# Get the default resume
curl http://localhost:8080/api/resumes/default

# Create a new version from default
curl -X POST http://localhost:8080/api/resumes \
  -H "Content-Type: application/json" \
  -d '{"label": "Technical Focus"}'

# Edit the new version's summary
curl -X PUT http://localhost:8080/api/resumes/2/summary \
  -H "Content-Type: application/json" \
  -d '{"text": "Experienced software engineer with focus on distributed systems..."}'

# Add a skill to the new version
curl -X POST http://localhost:8080/api/resumes/2/skills/entries \
  -H "Content-Type: application/json" \
  -d '{"name": "Kubernetes", "category": "Infrastructure"}'

# Set the new version as default
curl -X PUT http://localhost:8080/api/resumes/2/default

# Verify default changed
curl http://localhost:8080/api/resumes
```

### 2. Application CRUD

```bash
# Create an application
curl -X POST http://localhost:8080/api/applications \
  -H "Content-Type: application/json" \
  -d '{"company": "Acme Corp", "position": "Senior Engineer", "description": "Looking for...", "resume_version_id": 2}'

# List applications
curl http://localhost:8080/api/applications

# Filter by status
curl "http://localhost:8080/api/applications?status=Interested"

# Search
curl "http://localhost:8080/api/applications?q=Acme"

# Update status
curl -X PUT http://localhost:8080/api/applications/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Applied"}'
```

### 3. Contacts

```bash
# Add a contact
curl -X POST http://localhost:8080/api/applications/1/contacts \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "role": "Recruiter", "email": "jane@acme.com"}'

# List contacts
curl http://localhost:8080/api/applications/1/contacts
```

### 4. Communications

```bash
# Log a sent email
curl -X POST http://localhost:8080/api/applications/1/communications \
  -H "Content-Type: application/json" \
  -d '{"type": "email", "direction": "sent", "subject": "Application follow-up", "body": "Hi Jane...", "date": "2026-02-17", "contact_id": 1, "status": "sent"}'

# Log a draft
curl -X POST http://localhost:8080/api/applications/1/communications \
  -H "Content-Type: application/json" \
  -d '{"type": "email", "direction": "sent", "subject": "Thank you note", "body": "Dear Jane...", "date": "2026-02-18", "status": "draft"}'

# Progress draft to ready
curl -X PUT http://localhost:8080/api/applications/1/communications/2 \
  -H "Content-Type: application/json" \
  -d '{"status": "ready"}'
```

### 5. AI Context

```bash
# Get full application context for AI
curl http://localhost:8080/api/applications/1/context
```

## MCP Testing (via Claude)

```
# In Claude with persona MCP server configured:

"List my resumes"              → calls list_resumes
"Show my default resume"       → calls get_resume (no id)
"Create a Technical Focus resume" → calls create_resume with label
"Get the Acme Corp application context" → calls get_application_context
```
