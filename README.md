# Persona MCP Server

An MCP (Model Context Protocol) server that exposes personal data — starting with resume management — to AI assistants.

## What it does

- Stores resume data in a local SQLite database (auto-created on first use)
- Exposes MCP tools for retrieving and updating contact info, experience, education, skills, and summary
- Automatic schema migrations — upgrades are seamless with no data loss

## Data storage

Resume data is stored in a SQLite database at `~/.persona/persona.db`. The database and schema are created automatically on first run — no setup required.

Override the data directory with:

```bash
export PERSONA_DATA_DIR=/path/to/your/data
```

### Schema migrations

The database schema is versioned using SQLite's `PRAGMA user_version`. When you upgrade to a new version, migrations are applied automatically on startup. Each migration runs in a transaction — if it fails, the database is left unchanged.

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
# Export your GitHub PAT
export GITHUB_PAT=<your-github-pat>

# Add the GitHub MCP server
claude mcp add-json github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer '"$GITHUB_PAT"'"}}'

# Ask Claude to create a PR, then remove the server to save tokens
claude mcp remove github
```