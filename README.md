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

Data is stored in a `data/` directory, which is created automatically.

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

## Development

The following `make` commands are available for development:

| Command     | Description                                       |
|-------------|---------------------------------------------------|
| `make check`  | Run all checks (lint, types, tests) for all code. |
| `make test`   | Run tests.                                        |
| `make lint`   | Check for linting and formatting errors.          |
| `make format` | Automatically format all code.                    |
| `make run`    | Start the application using Docker Compose.       |
