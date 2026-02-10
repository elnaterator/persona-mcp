# Persona MCP Server

An MCP (Model Context Protocol) server that exposes personal data — starting with resume management — to AI assistants.

## What it does

- Reads and writes resume data from a local Markdown file with YAML front-matter
- Exposes MCP tools for retrieving and updating contact info, experience, education, skills, and summary
- Auto-creates the expected directory structure on startup

## Data directory

Defaults to `~/.persona/`. Override with:

```bash
export PERSONA_DATA_DIR=/path/to/your/data
```

Resume data lives at `jobs/resume/resume.md` under the data root. Future features will use sibling directories under `jobs/`.

## Resume format

```markdown
---
name: Jane Doe
email: jane@example.com
phone: 555-0100
location: San Francisco, CA
linkedin: https://linkedin.com/in/janedoe
website: https://janedoe.dev
github: https://github.com/janedoe
---

## Summary

Software engineer with 10 years of experience...

## Experience

### Senior Engineer — Acme Corp
*Jan 2020 – Present | San Francisco, CA*
- Led migration to microservices architecture

## Education

### B.S. Computer Science — MIT
*2010 – 2014*

## Skills

- **Languages**: Python, TypeScript, Go
- **Frameworks**: FastAPI, React
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `PERSONA_DATA_DIR` | Data directory path | `~/.persona/` |
| `LOG_LEVEL` | Logging level (Python `logging` to stderr) | `INFO` |
