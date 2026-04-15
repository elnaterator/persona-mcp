# Persona MCP Server

Personal data server for resume + job application management. AI workflow support built in.

## Features

- **Accomplishment Tracking**: Record career accomplishments in STAR format (Situation, Task, Action, Result). Tag for filtering. Use to craft job application materials.
- **Job Application Tracking**: Track applications from "Interested" to "Offer".
- **Resume Versioning**: Multiple resume versions, tailored per job.
- **Connect Tab**: Generate Clerk API key + copy-ready config commands for Claude Code, Cursor, GitHub Copilot, Amazon Kiro. Connect any AI coding assistant via MCP.
- **Web UI**: Clean interface for data management. Deep links + bookmarks supported — navigate directly via URL. Refresh stays on current view.
- **REST + MCP APIs**: Programmatic access via REST or MCP. `/mcp` endpoint supports dual auth: Clerk session JWTs (browser) and Clerk API keys (AI coding assistants).
- **Docker Support**: Run entire app with single command.

## Quick Start

**Prerequisites:**

1. [Docker](https://docs.docker.com/get-docker/) + `make`
2. [Clerk](https://clerk.com) account (free tier sufficient)
3. Copy `.env.example` to `.env` and populate Clerk env vars (see `.env.example` for required keys)

```bash
make run
```

Starts app + `postgres:16-alpine` container. Data persists in named Docker volume (`pg-data`) across restarts.

Once running:

- **Web UI**: `http://localhost:8000/`
- **REST API**: `http://localhost:8000/api`
- **MCP Endpoint**: `http://localhost:8000/mcp`

## Configure

| Variable | Description |
|---|---|
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key (`pk_test_...`) |
| `VITE_MCP_SERVER_URL` | MCP server URL for Connect tab (e.g. `https://your-server.com/mcp`) |
| `CLERK_JWKS_URL` | Clerk JWKS endpoint |
| `CLERK_ISSUER` | Clerk issuer URL |
| `CLERK_SECRET_KEY` | Clerk secret key — required, server fails to start if missing |
| `CLERK_WEBHOOK_SECRET` | Webhook signing secret from Clerk dashboard |

Copy `.env.example` to `.env` and fill in values.

## Deploy to AWS (optional)

Infra as code in `infra/` using Terraform + AWS Lambda (container image). See **[docs/deployment.md](docs/deployment.md)** for the full guide including bootstrap, first-time provisioning, secrets setup, CI/CD, and teardown.

```bash
make deploy ENV=dev   # or prod
```

## Developer Setup

### Required tools

Install once before any `make` targets:

| Tool | Version | Install |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Node.js](https://nodejs.org/en/download) | 20+ | Official installer or preferred version manager |
| [Docker](https://docs.docker.com/get-docker/) | Any | Official installer |
| [Terraform](https://developer.hashicorp.com/terraform/install) | 1.7+ | Official installer (infra work only) |
| [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) | 2.x | Official installer (infra work only) |

### Install managed dependencies

```bash
make setup
```

Installs Python packages (`uv sync`) + Node packages (`npm ci`). `checkov` fetched automatically on first use via `uvx`.

## Make Targets

```bash
make check   # lint + typecheck + test (frontend + backend)
make run     # start app via Docker Compose
make help    # list all targets
```
