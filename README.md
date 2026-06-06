# Persona MCP Server

Personal data server for resume + job application management. AI workflow support built in.

## Features

- **Accomplishment Tracking**: Record career accomplishments in STAR format (Situation, Task, Action, Result). Tag for filtering. Use to craft job application materials.
- **Job Application Tracking**: Track applications from "Interested" to "Offer".
- **Resume Versioning**: Multiple resume versions, tailored per job.
- **Connect Tab**: Copy-ready config for Claude Code, Cursor, GitHub Copilot, Amazon Kiro. MCP client opens a browser to sign in via OAuth — no API key to manage.
- **Web UI**: Clean interface for data management. Deep links + bookmarks supported — navigate directly via URL. Refresh stays on current view.
- **REST + MCP APIs**: Programmatic access via REST or MCP. `/mcp` uses standard OAuth2 bearer tokens (RFC 9728 resource server); assistant authenticates via PKCE + browser sign-in.
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
| `PERSONA_PUBLIC_URL` | Externally reachable base URL (e.g. `https://persona.example.com`) — required; used as OAuth2 resource identifier and metadata base |
| `CLERK_JWKS_URL` | Clerk JWKS endpoint |
| `CLERK_ISSUER` | Clerk issuer URL |
| `CLERK_WEBHOOK_SECRET` | Webhook signing secret from Clerk dashboard |

### Keyless OAuth connect flow

MCP clients (Claude Code, Cursor, etc.) connect via standard OAuth2 (RFC 9728 + DCR):

1. Client sends unauthenticated request to `/mcp` → server returns `401` with `WWW-Authenticate` header pointing to `/.well-known/oauth-protected-resource/mcp`.
2. Client fetches the metadata document → discovers the Clerk authorization server.
3. Client registers itself dynamically (RFC 7591) and performs a PKCE browser sign-in.
4. Client receives a resource-bound access token and calls `/mcp` with `Bearer <token>`.

No API key to generate or paste. Add the bare URL in your assistant's MCP config:

```bash
# Claude Code
claude mcp add --transport http persona https://your-persona-server.com/mcp

# Cursor / Kiro — .cursor/mcp.json or .kiro/settings/mcp.json
{ "mcpServers": { "persona": { "url": "https://your-persona-server.com/mcp" } } }
```

### Clerk manual setup (required before MCP auth works end-to-end)

1. Enable Dynamic Client Registration in Clerk Dashboard (OAuth Applications / OAuth2 server settings). Confirm `https://<frontend-api>/.well-known/oauth-authorization-server` advertises `registration_endpoint` + `code_challenge_methods_supported`.
2. Confirm Clerk allows DCR loopback/dynamic redirect URIs (CLI clients use `http://localhost:<port>/callback`).
3. Confirm Clerk honors `resource` indicator → mints access tokens with `aud=<PERSONA_PUBLIC_URL>/mcp`.

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
