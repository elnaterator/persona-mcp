# Persona MCP Server

A personal data server that helps you manage your resume and job applications, with support for AI-assisted workflows.

## Features

- **Accomplishment Tracking**: Record and manage career accomplishments using the STAR format (Situation, Task, Action, Result). Tag accomplishments for easy filtering and use them to craft compelling job application materials.
- **Job Application Tracking**: Manage job applications from "Interested" to "Offer".
- **Resume Versioning**: Maintain multiple resume versions and tailor them for specific jobs.
- **Web UI**: A clean web interface for managing your data.
- **REST + MCP APIs**: Access your data programmatically via a REST API or the Model Context Protocol (MCP).
- **Docker Support**: Run the entire application with a single command.

## Quick Start

The recommended way to run the Persona MCP Server is with Docker.

1.  **Prerequisites**:
    *   [Docker](https://docs.docker.com/get-docker/) installed and running.
    *   `make` installed.

2.  **Run the application**:

    ```bash
    git clone https://github.com/elnaterator/persona-mcp.git
    cd persona-mcp
    make run
    ```

3.  **Access the application**:
    *   **Web UI**: `http://localhost:8000/`
    *   **REST API**: `http://localhost:8000/api`
    *   **MCP Endpoint**: `http://localhost:8000/mcp`

`make run` automatically starts a `postgres:16-alpine` container alongside the app.
Data is persisted in a named Docker volume (`pg-data`) and survives restarts.

## Usage

### REST API Endpoints

The API is available at `http://localhost:8000/api`.

**Accomplishments**

*   `GET /api/accomplishments`: List all accomplishments (summaries: title, date, tags). Supports `?tag=X` to filter by tag and `?q=Y` for text search.
*   `GET /api/accomplishments/tags`: Get a sorted list of all unique tags across accomplishments.
*   `POST /api/accomplishments`: Create a new accomplishment (title required; situation, task, action, result, accomplishment_date, tags optional).
*   `GET /api/accomplishments/{id}`: Get a single accomplishment with full STAR content.
*   `PATCH /api/accomplishments/{id}`: Partially update an accomplishment (only provided fields are changed).
*   `DELETE /api/accomplishments/{id}`: Delete an accomplishment.

**Resumes**

*   `GET /api/resumes`: List all resume versions.
*   `GET /api/resumes/{id}`: Get a specific resume version.
*   `POST /api/resumes`: Create a new resume version.
*   `PUT /api/resumes/{id}/default`: Set a resume version as default.
*   `GET /api/applications`: List all job applications.
*   `POST /api/applications`: Create a new job application.
*   `GET /api/applications/{id}`: Get a specific job application.
*   `PUT /api/applications/{id}`: Update a job application.
*   `DELETE /api/applications/{id}`: Delete a job application.
*   `GET /api/applications/{id}/contacts`: List contacts for an application.
*   `POST /api/applications/{id}/contacts`: Add a contact to an application.
*   `GET /api/applications/{id}/communications`: List communications for an application.
*   `POST /api/applications/{id}/communications`: Add a communication to an application.
*   `GET /api/applications/{id}/context`: Get full context for an application (for AI).

### MCP Tools

The MCP server is available at `http://localhost:8000/mcp`.
AI assistants can use tools like:

**Accomplishment tools**

*   `list_accomplishments`: List accomplishments with optional `tag` and `q` filter params. Returns summaries (no STAR body).
*   `get_accomplishment`: Get full STAR detail for a single accomplishment by `id`.
*   `create_accomplishment`: Create a new accomplishment. Required: `title`. Optional: `situation`, `task`, `action`, `result`, `accomplishment_date` (YYYY-MM-DD), `tags` (list of strings).
*   `update_accomplishment`: Partially update an accomplishment by `id`. All fields except `id` are optional.
*   `delete_accomplishment`: Delete an accomplishment by `id`.

**Resume and application tools**

*   `list_resumes`: List all available resume versions.
*   `get_resume`: Get a specific resume version (or the default).
*   `create_resume`: Create a new resume version.
*   `get_application_context`: Get all relevant data for a job application to assist with AI tasks.
*   `create_application`: Create a new job application.
*   `update_application`: Update an existing job application.
*   `add_contact_to_application`: Add a contact to a job application.
*   `add_communication_to_application`: Add a communication to a job application.

## Authentication Setup

Persona uses [Clerk](https://clerk.com) for authentication. You must configure Clerk before running the application.

### Prerequisites

- A Clerk account and application (free tier is sufficient)
- Google and/or GitHub OAuth configured in the Clerk dashboard (optional, for social login)

### Required Environment Variables

| Variable | Where to set | Description |
|---|---|---|
| `VITE_CLERK_PUBLISHABLE_KEY` | `frontend/.env.local` | Clerk publishable key (`pk_test_...`) |
| `CLERK_JWKS_URL` | backend env | Clerk JWKS endpoint (`https://<instance>.clerk.accounts.dev/.well-known/jwks.json`) |
| `CLERK_ISSUER` | backend env | Clerk issuer URL (`https://<instance>.clerk.accounts.dev`) |
| `CLERK_WEBHOOK_SECRET` | backend env | Webhook signing secret (`whsec_...`) from the Clerk webhooks dashboard |

Copy `frontend/.env.local.example` to `frontend/.env.local` and fill in your Clerk publishable key.

See [`specs/008-authentication/quickstart.md`](specs/008-authentication/quickstart.md) for step-by-step setup instructions including social login configuration and webhook setup.

### Database Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PERSONA_DB_URL` | *(required)* | PostgreSQL DSN, e.g. `postgresql://persona:persona@localhost:5432/persona` |
| `PERSONA_DB_POOL_MIN` | `1` | Minimum connections in the pool |
| `PERSONA_DB_POOL_MAX` | `10` | Maximum connections in the pool |

`make run` sets `PERSONA_DB_URL` automatically via `docker-compose.yml`.

For local development outside Docker (e.g. `make run-local`), start Postgres first then export the variable:

```bash
docker compose up postgres -d
export PERSONA_DB_URL=postgresql://persona:persona@localhost:5432/persona
make run-local
```

## Infrastructure

The application is deployed to AWS Lambda (container image) using Terraform. All infrastructure is defined as code in the `infra/` directory.

### Directory structure

```
infra/
├── modules/
│   ├── lambda/        # ECR repo, IAM role, Lambda function, Function URL
│   └── observability/ # CloudWatch log group + error alarm
├── dev/               # Dev environment root (separate state)
└── prod/              # Prod environment root (separate state)
```

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Terraform](https://developer.hashicorp.com/terraform/install) | 1.7+ | Infrastructure provisioning |
| [AWS CLI](https://aws.amazon.com/cli/) | 2.x | AWS authentication and ECR push |
| [Docker](https://docs.docker.com/get-docker/) | Any | Build and push container images |

### CI validation

Every pull request that modifies `infra/**` automatically runs:
1. **Terraform format check** — `terraform fmt -check -recursive`
2. **Checkov security scan** — static analysis for misconfigurations
3. **Terraform plan** — for both `dev` and `prod` (read-only, no apply)

**CI never runs `terraform apply`.** All provisioning is performed manually by the developer.

### Manual provisioning

Follow the step-by-step runbook at [`specs/010-aws-infra/quickstart.md`](specs/010-aws-infra/quickstart.md) to:
- Bootstrap remote state (S3 + DynamoDB, one-time setup)
- Provision a new environment
- Deploy application updates
- Set SSM secrets before first apply

### Terraform make targets

| Command | Description |
|---------|-------------|
| `make tf-lint` | Check Terraform formatting (`terraform fmt -check -recursive infra/`) |
| `make tf-check` | `tf-lint` + Checkov security scan |

`make check` includes `tf-lint` automatically.

## Developer Setup

### Required tools (install once, manually)

These are binary tools that must be on your `PATH` before running any `make` targets. Use the official installer for your OS — no specific package manager is assumed.

| Tool | Version | Install |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Node.js](https://nodejs.org/en/download) | 20+ | Official installer or your preferred version manager |
| [Docker](https://docs.docker.com/get-docker/) | Any | Official installer |
| [Terraform](https://developer.hashicorp.com/terraform/install) | 1.7+ | Official installer (infrastructure work only) |
| [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) | 2.x | Official installer (infrastructure work only) |

### Install managed dependencies

After cloning and installing the required tools above, run:

```bash
make setup
```

This installs all automatically managed dependencies:
- **Python packages** (`uv sync` in `backend/`) — installs the virtualenv and all dev dependencies declared in `pyproject.toml`
- **Node packages** (`npm ci` in `frontend/`) — installs exact versions from `package-lock.json`

`checkov` (used by `make tf-check`) is **not** pre-installed — it is fetched and cached automatically on first run via `uvx`, which is bundled with `uv`.

## Development

The following `make` commands are available for development:

| Command     | Description                                       |
|-------------|---------------------------------------------------|
| `make check`  | Run all checks (lint, types, tests) for all code. |
| `make test`   | Run tests.                                        |
| `make lint`   | Check for linting and formatting errors.          |
| `make format` | Automatically format all code.                    |
| `make run`    | Start the application using Docker Compose.       |
