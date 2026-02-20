# API Contracts: Authentication & Multi-user (rev 1)

**Date**: 2026-02-18
**Feature**: 008-authentication

## Authentication Overview

All existing API endpoints (except for the webhook listener) now require a valid Clerk JWT passed in the `Authorization` header as a Bearer token.

**Header**: `Authorization: Bearer <clerk_jwt_token>`

### Global Error Responses

| Status Code | Description |
|-------------|-------------|
| `401 Unauthorized` | Missing or invalid token. Includes cases where token is expired. |
| `403 Forbidden` | Valid token but user is attempting to access a resource they do not own (e.g., another user's resume). |

---

## New Endpoints

### `POST /api/webhooks/clerk`

Webhook listener for Clerk events. Secured via Svix signature verification.

**Headers**:
- `svix-id`: Unique message ID
- `svix-timestamp`: Message timestamp
- `svix-signature`: HMAC signature

**Request Body (Example `user.deleted`)**:
```json
{
  "data": {
    "id": "user_2S...",
    "deleted": true,
    "object": "user"
  },
  "object": "event",
  "type": "user.deleted"
}
```

**Response**:
- `200 OK`: Event processed successfully (e.g., data hard-deleted).
- `400 Bad Request`: Invalid signature or malformed payload.

---

## Impact on Existing Endpoints

Every endpoint defined in previous specs (e.g., `006-job-applications/contracts/rest-api.md`) is updated as follows:

### 1. Ownership Filtering
All `GET` list endpoints (e.g., `GET /api/resumes`, `GET /api/applications`) implicitly filter by the `user_id` extracted from the JWT.
- **Request**: `GET /api/resumes`
- **Logic**: `SELECT * FROM resume_version WHERE user_id = :current_user_id`

### 2. Ownership Verification
All detail and mutation endpoints (e.g., `GET /api/resumes/{id}`, `PUT /api/applications/{id}`) verify that the resource belongs to the `current_user_id`.
- **Logic**: If resource exists but `resource.user_id != :current_user_id`, return `403 Forbidden`.
- **Note**: Returning `404 Not Found` is also an acceptable pattern to avoid leaking resource existence, but `403` is preferred for explicit multi-user debugging.

### 3. Automatic Association
All creation endpoints (e.g., `POST /api/resumes`, `POST /api/applications`) automatically set the `user_id` to the `current_user_id`.
- **Request**: `POST /api/applications` (payload excludes `user_id`)
- **Logic**: `INSERT INTO application (user_id, company, ...) VALUES (:current_user_id, :company, ...)`

---

## MCP Tool Authentication

MCP tools (e.g., `read_resume`, `write_application`) now require an authenticated context.

### HTTP (streamable-http) Transport
When using the MCP server via streamable-http, the `Authorization: Bearer <clerk_jwt_token>` header must be provided. Tool execution will fail with `401` if the header is missing or invalid. The JWT is validated identically to the REST API (JWKS + python-jose).

### Stdio Transport (Local Development)
For local CLI usage where HTTP headers are not applicable, an environment variable is used to provide the user context:
- `PERSONA_USER_ID`: Directly set the user context (for testing/local dev without a full JWT flow).
- `PERSONA_CLERK_TOKEN`: Provide a JWT for full validation during local integration testing.
