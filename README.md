# Persona MCP Server

A personal data server that helps you manage your resume and job applications, with support for AI-assisted workflows.

## Features

- **Accomplishment Tracking**: Record and manage career accomplishments using the STAR format (Situation, Task, Action, Result). Tag accomplishments for easy filtering and use them to craft compelling job application materials.
- **Job Application Tracking**: Manage job applications from "Interested" to "Offer".
- **Resume Versioning**: Maintain multiple resume versions and tailor them for specific jobs.
- **Connect Tab**: Generate a Clerk API key and get copy-ready configuration commands for Claude Code, Cursor, GitHub Copilot, and Amazon Kiro — connect any AI coding assistant directly to your personal data via MCP.
- **Web UI**: A clean web interface for managing your data.
- **REST + MCP APIs**: Access your data programmatically via a REST API or the Model Context Protocol (MCP). The `/mcp` endpoint supports dual authentication: Clerk session JWTs (browser) and Clerk API keys (AI coding assistants).
- **Docker Support**: Run the entire application with a single command.

## Quick Start

```bash
git clone https://github.com/elnaterator/persona-mcp.git
cd persona-mcp
make run
```

Requires [Docker](https://docs.docker.com/get-docker/) and `make`. Before running, configure [Clerk authentication](#authentication) and set the `PERSONA_DB_URL` environment variable (handled automatically by `docker-compose.yml` for local runs — see [Database](#database) for details).

`make run` starts a `postgres:16-alpine` container alongside the app. Data is persisted in a named Docker volume (`pg-data`) and survives restarts.

Once running:

- **Web UI**: `http://localhost:8000/`
- **REST API**: `http://localhost:8000/api`
- **MCP Endpoint**: `http://localhost:8000/mcp`

## Configuration

### Authentication

Persona uses [Clerk](https://clerk.com) for authentication. You need a Clerk account (free tier is sufficient) before running the application.

| Variable | Where to set | Description |
|---|---|---|
| `VITE_CLERK_PUBLISHABLE_KEY` | `frontend/.env.local` | Clerk publishable key (`pk_test_...`) |
| `VITE_MCP_SERVER_URL` | `frontend/.env.local` | MCP server URL shown in Connect tab config commands (e.g. `https://your-server.com/mcp`). Defaults to `https://your-persona-server.com/mcp` if unset. |
| `CLERK_JWKS_URL` | backend env | Clerk JWKS endpoint (`https://<instance>.clerk.accounts.dev/.well-known/jwks.json`) |
| `CLERK_ISSUER` | backend env | Clerk issuer URL (`https://<instance>.clerk.accounts.dev`) |
| `CLERK_SECRET_KEY` | backend env | **Required** — Clerk secret key (`sk_test_...` or `sk_live_...`) for MCP dual-auth (session JWTs + API keys). The server will fail to start if this is missing. |
| `CLERK_WEBHOOK_SECRET` | backend env | Webhook signing secret (`whsec_...`) from the Clerk webhooks dashboard |

Copy `frontend/.env.local.example` to `frontend/.env.local` and fill in your Clerk publishable key and MCP server URL.

See [`specs/008-authentication/quickstart.md`](specs/008-authentication/quickstart.md) for step-by-step Clerk setup including social login and webhook configuration.

### Database

| Variable | Default | Description |
|---|---|---|
| `PERSONA_DB_URL` | *(required)* | PostgreSQL DSN, e.g. `postgresql://persona:persona@localhost:5432/persona` |
| `PERSONA_DB_POOL_MIN` | `1` | Minimum connections in the pool |
| `PERSONA_DB_POOL_MAX` | `10` | Maximum connections in the pool |

`make run` sets `PERSONA_DB_URL` automatically via `docker-compose.yml`. For local development outside Docker (e.g. `make run-local`):

```bash
docker compose up postgres -d
export PERSONA_DB_URL=postgresql://persona:persona@localhost:5432/persona
make run-local
```

## Usage

### REST API Endpoints

The API is available at `http://localhost:8000/api`.

**Accomplishments**

- `GET /api/accomplishments` — List all accomplishments (summaries: title, date, tags). Supports `?tag=X` and `?q=Y`.
- `GET /api/accomplishments/tags` — Get a sorted list of all unique tags.
- `POST /api/accomplishments` — Create a new accomplishment (`title` required).
- `GET /api/accomplishments/{id}` — Get a single accomplishment with full STAR content.
- `PATCH /api/accomplishments/{id}` — Partially update an accomplishment.
- `DELETE /api/accomplishments/{id}` — Delete an accomplishment.

**Resumes**

- `GET /api/resumes` — List all resume versions.
- `GET /api/resumes/{id}` — Get a specific resume version.
- `POST /api/resumes` — Create a new resume version.
- `PUT /api/resumes/{id}/default` — Set a resume version as default.

**Applications**

- `GET /api/applications` — List all job applications.
- `POST /api/applications` — Create a new job application.
- `GET /api/applications/{id}` — Get a specific job application.
- `PUT /api/applications/{id}` — Update a job application.
- `DELETE /api/applications/{id}` — Delete a job application.
- `GET /api/applications/{id}/contacts` — List contacts for an application.
- `POST /api/applications/{id}/contacts` — Add a contact to an application.
- `GET /api/applications/{id}/communications` — List communications for an application.
- `POST /api/applications/{id}/communications` — Add a communication to an application.
- `GET /api/applications/{id}/context` — Get full application context (for AI).

### MCP Tools

The MCP server is available at `http://localhost:8000/mcp`.

**Accomplishment tools**

- `list_accomplishments` — List accomplishments with optional `tag` and `q` filters. Returns summaries only.
- `get_accomplishment` — Get full STAR detail for a single accomplishment by `id`.
- `create_accomplishment` — Create a new accomplishment. Required: `title`. Optional: `situation`, `task`, `action`, `result`, `accomplishment_date` (YYYY-MM-DD), `tags`.
- `update_accomplishment` — Partially update an accomplishment by `id`.
- `delete_accomplishment` — Delete an accomplishment by `id`.

**Resume and application tools**

- `list_resumes` — List all available resume versions.
- `get_resume` — Get a specific resume version (or the default).
- `create_resume` — Create a new resume version.
- `get_application_context` — Get all relevant data for a job application to assist with AI tasks.
- `create_application` — Create a new job application.
- `update_application` — Update an existing job application.
- `add_contact_to_application` — Add a contact to a job application.
- `add_communication_to_application` — Add a communication to a job application.

## Infrastructure

The application is deployed to AWS Lambda (container image) using Terraform. All infrastructure is defined as code in the `infra/` directory.

```
infra/
├── modules/
│   ├── lambda/        # ECR repo, IAM role, Lambda function, Function URL
│   └── observability/ # CloudWatch log group + error alarm
├── dev/               # Dev environment root (separate state)
└── prod/              # Prod environment root (separate state)
```

Every pull request that modifies `infra/**` automatically runs a format check, Checkov security scan, and `terraform plan` for both environments. **CI never runs `terraform apply`** — all provisioning is performed manually.

See **[docs/deployment.md](docs/deployment.md)** for the full deployment guide, including:

- One-time bootstrap (S3 + DynamoDB state backends)
- First-time provisioning (two-phase apply)
- Setting SSM secrets (database URL, Clerk keys)
- Subsequent deploys via `make deploy ENV=dev`
- Setting up GitHub Actions CI (OIDC)
- Destroying an environment

## Developer Setup

### Required tools

Install these once before running any `make` targets:

| Tool | Version | Install |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Node.js](https://nodejs.org/en/download) | 20+ | Official installer or your preferred version manager |
| [Docker](https://docs.docker.com/get-docker/) | Any | Official installer |
| [Terraform](https://developer.hashicorp.com/terraform/install) | 1.7+ | Official installer (infrastructure work only) |
| [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) | 2.x | Official installer (infrastructure work only) |

### Install managed dependencies

```bash
make setup
```

Installs Python packages (`uv sync`) and Node packages (`npm ci`). `checkov` is fetched automatically on first use via `uvx` — no separate install needed.

## Make Targets

| Command | Description |
|---------|-------------|
| `make run` | Start the application via Docker Compose |
| `make run-local` | Build frontend then run backend locally |
| `make check` | Lint + typecheck + test (frontend, backend, and Terraform fmt) |
| `make test` | Run all tests |
| `make lint` | Check for linting and formatting errors |
| `make format` | Auto-format all code |
| `make build` | Build frontend then backend |
| `make tf-lint` | Check Terraform formatting (`terraform fmt -check -recursive infra/`) |
| `make tf-check` | `tf-lint` + Checkov security scan |
| `make deploy ENV=dev\|prod` | Build image, push to ECR, and run `terraform apply` |
