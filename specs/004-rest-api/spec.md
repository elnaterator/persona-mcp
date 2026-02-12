# Feature Specification: REST API & Remote MCP Server with Docker Support

**Feature Branch**: `feat-004-rest-api`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "Add a REST API for CRUD operations on resume data, serve MCP via streamable-http as a remote MCP server, both available when the app is running, sharing core business logic and database connection, with Docker container support."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Resume via REST API (Priority: P1)

As a developer or application, I want to manage my resume data through a standard REST API so that I can integrate resume management into web applications, scripts, or third-party tools without needing an MCP client.

**Why this priority**: The REST API is the primary new capability requested. It enables the broadest range of integrations and is the most commonly understood interface for web services.

**Independent Test**: Can be fully tested by sending HTTP requests (GET, PUT, POST, DELETE) to resume endpoints and verifying correct data is returned/modified. Delivers value as a standalone CRUD API for resume data.

**Acceptance Scenarios**:

1. **Given** a running application, **When** a client sends a GET request to retrieve the full resume, **Then** the response contains all resume sections (contact, summary, experience, education, skills) as structured JSON with a success status code.
2. **Given** a running application, **When** a client sends a GET request for a specific resume section (e.g., experience), **Then** only that section's data is returned as structured JSON.
3. **Given** a running application, **When** a client sends a PUT request to update contact info or summary with valid data, **Then** the data is persisted and the response confirms the update.
4. **Given** a running application, **When** a client sends a POST request to add a new experience entry with valid data, **Then** the entry is added and the response includes the created entry.
5. **Given** a running application, **When** a client sends a DELETE request to remove an experience entry by index, **Then** the entry is removed and the response confirms the removal.
6. **Given** a running application, **When** a client sends a request with invalid data (missing required fields, invalid section name, out-of-range index), **Then** the response includes an appropriate error status code and a descriptive error message.

---

### User Story 2 - Access MCP Server Remotely via HTTP (Priority: P2)

As an MCP client application, I want to connect to the Persona MCP server over HTTP (streamable-http transport) so that I can use MCP tools from remote clients without requiring local stdio access.

**Why this priority**: Transitioning MCP from stdio to streamable-http is essential for remote access and aligns with the unified server architecture. It enables MCP clients that cannot use stdio (e.g., web-based AI agents).

**Independent Test**: Can be fully tested by connecting an MCP client to the HTTP endpoint and invoking existing MCP tools (get_resume, update_section, etc.). Delivers value as a remotely accessible MCP server.

**Acceptance Scenarios**:

1. **Given** a running application, **When** an MCP client connects via streamable-http transport, **Then** the client can discover and invoke all existing MCP tools.
2. **Given** a running application, **When** an MCP client invokes `get_resume` over streamable-http, **Then** the response is identical to what would be returned via stdio transport.
3. **Given** a running application, **When** an MCP client invokes a write tool (e.g., `add_entry`) over streamable-http, **Then** the data is persisted and visible through both MCP and REST API.

---

### User Story 3 - Unified Server with Shared State (Priority: P2)

As a user running the application, I want both the REST API and the MCP server to be available simultaneously from a single process, sharing the same database, so that changes made through one interface are immediately visible through the other.

**Why this priority**: Shared state is critical for data consistency. Without it, users would see stale or conflicting data depending on which interface they use.

**Independent Test**: Can be tested by making a write through the REST API and reading through MCP (or vice versa), verifying the change is immediately visible. Delivers value by ensuring a consistent single-source-of-truth experience.

**Acceptance Scenarios**:

1. **Given** a running application, **When** a user adds an experience entry via the REST API, **Then** calling `get_resume` via MCP immediately returns the new entry.
2. **Given** a running application, **When** a user updates contact info via MCP, **Then** a GET request to the REST API contact endpoint immediately returns the updated info.
3. **Given** a running application, **When** both interfaces are used concurrently, **Then** no data corruption or race conditions occur.

---

### User Story 4 - Run Application in Docker Container (Priority: P3)

As a user or operator, I want to run the Persona application in a Docker container so that I can deploy it consistently across environments without installing Python or dependencies on the host.

**Why this priority**: Docker support enables deployment flexibility and reproducibility but is not required for core functionality to work.

**Independent Test**: Can be tested by building the Docker image, running a container, and verifying both REST API and MCP endpoints respond correctly. Delivers value as a portable, self-contained deployment option.

**Acceptance Scenarios**:

1. **Given** a Dockerfile in the repository, **When** a user builds the image, **Then** the build completes successfully without errors.
2. **Given** a built Docker image, **When** a user runs a container with default settings, **Then** both the REST API and MCP server are accessible from the host on a configurable port.
3. **Given** a running container, **When** the container is stopped and restarted with the same data volume, **Then** all previously stored resume data is preserved.
4. **Given** a running container, **When** a user sets environment variables for configuration (port, data directory, log level), **Then** the application respects those settings.

---

### Edge Cases

- What happens when a client sends a request to a non-existent resume section? The system returns a clear error with valid section names.
- What happens when a client tries to remove an entry at an index that doesn't exist? The system returns an error indicating the index is out of range.
- What happens when multiple concurrent requests modify the same data? SQLite WAL mode and busy timeout handle contention; the system does not corrupt data.
- What happens when the database file is missing on container startup? The system initializes a fresh database automatically (existing behavior).
- What happens when a client sends malformed JSON in a request body? The system returns a validation error with details about what was wrong.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a REST API with endpoints for reading the full resume, reading individual sections, updating singleton sections (contact, summary), and adding/updating/removing entries in list sections (experience, education, skills).
- **FR-002**: System MUST serve the MCP server via streamable-http transport, making all existing MCP tools accessible over HTTP.
- **FR-003**: The REST API and MCP server MUST run within a single application process, sharing the same database connection.
- **FR-004**: The REST API MUST return appropriate HTTP status codes (200 for success, 201 for creation, 400 for validation errors, 404 for not-found, 422 for invalid input).
- **FR-005**: The REST API MUST accept and return JSON for all request and response bodies.
- **FR-006**: The REST API and MCP server MUST reuse the same core business logic (the existing read/write tool functions and database layer), not duplicate it.
- **FR-007**: The application MUST be configurable via environment variables for port number, data directory, log level, and allowed CORS origins.
- **FR-012**: The REST API MUST include CORS headers with a configurable allow-list of origins to support browser-based UI consumers. When no origins are configured, CORS MUST default to restrictive (no cross-origin access).
- **FR-013**: The application MUST expose a dedicated health check endpoint that returns service status, suitable for use by Docker HEALTHCHECK, load balancers, and uptime monitors.
- **FR-008**: A Dockerfile MUST be provided that builds and runs the application, exposing the configured port.
- **FR-009**: The Docker container MUST support mounting an external volume for persistent database storage.
- **FR-010**: The application MUST start both the REST API and MCP server from a single command entry point.
- **FR-011**: The `persona` CLI entry point MUST default to starting the HTTP server (REST API + MCP streamable-http). A `--stdio` flag MUST be supported to run the MCP server in stdio mode for backward compatibility with local MCP clients (e.g., Claude Desktop).

### Key Entities

- **Resume**: The aggregate entity containing all sections (contact, summary, experience, education, skills). Already defined in the data model.
- **Resume Section**: An individual part of the resume (contact info, summary text, experience list, education list, skills list). Sections are either singleton (contact, summary) or list-based (experience, education, skills).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing resume CRUD operations are accessible through both REST API and MCP interfaces with identical data outcomes.
- **SC-002**: A single command starts the full application with both interfaces available.
- **SC-003**: Changes made through one interface (REST or MCP) are immediately visible through the other interface without restart.
- **SC-004**: The Docker image can be built and a container started with resume operations working within 60 seconds on a standard development machine.
- **SC-005**: All existing tests continue to pass, and new tests cover REST API endpoints and MCP-over-HTTP behavior.
- **SC-006**: The application starts and responds to requests within 5 seconds.

## Assumptions

- The REST API does not require authentication for this iteration. Authentication can be added in a future feature if needed.
- The application will listen on a single port, with the REST API and MCP streamable-http endpoint both accessible on that port (at different URL paths).
- The HTTP server (REST API + MCP streamable-http) is the default transport mode. The `--stdio` flag is available for backward compatibility with local MCP clients that require stdio transport.
- The Docker base image will be a minimal Python image to keep the container small.
- The default port will be configurable via environment variable with a sensible default (e.g., 8000).

## Clarifications

### Session 2026-02-11

- Q: Should the existing stdio MCP transport be retained alongside the new HTTP server, or dropped entirely? → A: HTTP server is the default; `--stdio` flag available for backward-compatible local MCP client usage.
- Q: Does the REST API need CORS support for browser-based consumers? → A: Yes, enable CORS with a configurable allow-list of origins. The API is intended for consumption by a web-based UI.
- Q: Should the application include a dedicated health check endpoint? → A: Yes, include a health endpoint for Docker HEALTHCHECK, load balancers, and uptime monitoring.
