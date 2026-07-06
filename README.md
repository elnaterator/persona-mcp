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
| `PERSONA_PUBLIC_URL` | Externally reachable base URL (e.g. `https://persona.example.com`) — required; the OAuth proxy advertises this as the authorization server and metadata base |
| `CLERK_JWKS_URL` | Clerk JWKS endpoint |
| `CLERK_ISSUER` | Clerk issuer URL |
| `CLERK_OAUTH_CLIENT_ID` | Client id of the static Clerk OAuth application the MCP proxy uses upstream |
| `CLERK_OAUTH_CLIENT_SECRET` | Client secret of that Clerk OAuth application |
| `CLERK_WEBHOOK_SECRET` | Webhook signing secret from Clerk dashboard |
| `FASTMCP_HOME` | Directory for FastMCP OAuth-proxy state (default OS data dir); mount a volume in prod so DCR registrations + encrypted upstream tokens survive restarts |

### Keyless OAuth connect flow

MCP clients (Claude Code, Cursor, etc.) connect via standard OAuth2. The server runs a
**DCR proxy** (FastMCP `OAuthProxy`): clients register and authorize against *us*, and we
proxy the flow upstream to Clerk through one fixed OAuth application. This removes the
loopback-redirect friction where a native client registers `http://localhost:PORT` but
sends `http://127.0.0.1:PORT` — both loopback hosts are accepted.

1. Client sends unauthenticated request to `/mcp` → server returns `401` with `WWW-Authenticate` pointing to `/.well-known/oauth-protected-resource/mcp`.
2. Client fetches the metadata → discovers **this server** as the authorization server.
3. Client registers dynamically (RFC 7591) with a loopback redirect, then does a PKCE browser sign-in; the consent screen redirects to Clerk to authenticate.
4. The proxy exchanges the Clerk code server-side, stores the Clerk token encrypted, and issues the client a reference JWT. Each `/mcp` call re-validates the stored Clerk token, so revocation at Clerk takes effect.

No API key to generate or paste. Add the bare URL in your assistant's MCP config:

```bash
# Claude Code
claude mcp add --transport http persona https://your-persona-server.com/mcp

# Cursor / Kiro — .cursor/mcp.json or .kiro/settings/mcp.json
{ "mcpServers": { "persona": { "url": "https://your-persona-server.com/mcp" } } }
```

### Clerk manual setup (required before MCP auth works end-to-end)

1. Create an OAuth application in Clerk Dashboard with redirect URI `<PERSONA_PUBLIC_URL>/auth/callback`; set its client id/secret as `CLERK_OAUTH_CLIENT_ID` / `CLERK_OAUTH_CLIENT_SECRET`.
2. Confirm `<CLERK_ISSUER>/.well-known/oauth-authorization-server` advertises `authorization_endpoint` / `token_endpoint` matching `<CLERK_ISSUER>/oauth/authorize` and `/oauth/token` (adjust the proxy config if Clerk's paths differ).
3. Clients register with the proxy, not with Clerk, so Clerk-side Dynamic Client Registration is no longer required and can be left disabled.

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
