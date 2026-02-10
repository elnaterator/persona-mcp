# Quickstart: Persona MCP Server

**Date**: 2026-02-09
**Feature**: 001-resume-mcp-server

## Prerequisites

- Python 3.11+
- `uv` package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))

## Setup

```bash
# Clone and enter the project
git clone <repo-url> personal-mcp
cd personal-mcp

# Install dependencies
uv sync

# Run the test suite
make check
```

## Running the Server

```bash
# Start via make
make run

# Or directly
uv run persona
```

The server communicates over STDIO. It is not meant to be used interactively — connect it to an MCP client (e.g., Claude Desktop).

## Configuration

| Environment Variable | Default       | Description                          |
|---------------------|---------------|--------------------------------------|
| `PERSONA_DATA_DIR`  | `~/.persona/` | Path to the persona data directory   |
| `LOG_LEVEL`         | `INFO`        | Logging level (DEBUG, INFO, WARNING) |

```bash
# Example: custom data directory
PERSONA_DATA_DIR=/path/to/my/data uv run persona
```

## Claude Desktop Integration

Add to your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "persona": {
      "command": "uvx",
      "args": ["persona"]
    }
  }
}
```

With a custom data directory:

```json
{
  "mcpServers": {
    "persona": {
      "command": "uvx",
      "args": ["persona"],
      "env": {
        "PERSONA_DATA_DIR": "/path/to/my/data"
      }
    }
  }
}
```

## Data Directory Structure

The server expects (and auto-creates) this structure under the data directory:

```
~/.persona/
└── jobs/
    └── resume/
        └── resume.md
```

## Resume File Format

`resume.md` uses YAML front-matter for contact info and Markdown sections for resume content:

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

- Led migration to microservices architecture

## Education

### M.S. Computer Science | Stanford University
- **Start**: 2016-09
- **End**: 2018-05

## Skills

### Programming Languages
- Python
- TypeScript
```

## Development

```bash
# Run tests
make test

# Run linter
make lint

# Run both (pre-commit check)
make check

# Format code
make format
```

## Available MCP Tools

Once connected, an AI assistant can use these tools:

**Read (P1)**:
- `get_resume` — Get the full resume as structured data
- `get_resume_section` — Get a specific section by name (contact, summary, experience, education, skills)

**Write (P2)**:
- `update_section` — Update contact info or summary
- `add_entry` — Add an entry to experience, education, or skills
- `update_entry` — Update an existing entry by index
- `remove_entry` — Remove an entry by index
