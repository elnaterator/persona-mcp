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

## Recommended Workflow

This project uses [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with [spec-kit](https://github.com/github/spec-kit) for Spec-Driven Development (SDD) and **git worktrees** for parallel feature development.

### Setting up a new feature

```bash
# From the main working tree, create a worktree with a new feature branch
git worktree add ../worktrees/feat-003-my-feature -b feat-003-my-feature

# Open the worktree in VS Code and start Claude Code from there
code ../worktrees/feat-003-my-feature
```

### Spec-driven development (inside the worktree)

1. `/speckit.specify [feature requirements]` — generates a spec directory and initial spec. Review, edit, and re-run to refine.
2. `/speckit.clarify` — identifies gaps in the spec and asks clarifying questions.
3. `/speckit.plan [tech details]` — generates an implementation plan. Review and iterate as needed.
4. `/speckit.tasks` — produces a task list from the plan. Review and iterate as needed.
5. `/speckit.analyze` — checks alignment across spec, plan, and tasks to ensure full coverage.
6. `/speckit.implement [scope]` — executes tasks (e.g., `phase 1` or `tasks 1-4`).
7. Commit changes — in chunks or all at once, depending on feature size.
8. Push the branch.
9. Enable the GitHub MCP server (see below) and have Claude create a PR.
10. Review CI, then merge to main.

### Cleaning up after merge

```bash
# Remove the worktree after merging
git worktree remove ../worktrees/feat-003-my-feature
```

### GitHub MCP server setup (for PR creation)

```bash
# Load env vars (includes GITHUB_PAT)
export $(grep -v '^#' .env | xargs)

# Add the GitHub MCP server
claude mcp add-json github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer '"$(grep GITHUB_PAT .env | cut -d '=' -f2)"'"}}'

# Ask Claude to create a PR, then remove the server to save tokens
claude mcp remove github
```