# Contract: MCP Endpoint Dual Authentication

**Feature**: `011-mcp-instructions`
**Endpoint**: `POST /mcp` (and all MCP protocol methods on this path)
**Transport**: Streamable-HTTP (FastMCP)
**Date**: 2026-02-27

---

## Overview

The `/mcp` endpoint MUST accept two token types in the `Authorization: Bearer <token>` header:

1. **Clerk session JWT** (prefix: none — standard JWT format `eyJ...`)
2. **Clerk native API key** (prefix: `ak_` — opaque string)

Both token types MUST yield an equivalent `current_user_id_var` ContextVar value for MCP tool execution.

---

## Authentication Contract

### Request

```
POST /mcp HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json
```

### Token Type Detection

Token type is determined by prefix matching (performed by Clerk SDK):

| Token prefix | Token type | Verification method |
|---|---|---|
| `eyJ...` (JWT) | `session_token` | JWKS public key (network or cached) |
| `ak_...` | `api_key` | Clerk `/api_keys/verify` (network call) |

### Success Response

When either token type is valid:

- `current_user_id_var` ContextVar is set to the Clerk user ID string (e.g., `user_2abc...`)
- MCP request proceeds to tool handler
- HTTP response determined by MCP protocol (200/204 per MCP spec)

### Failure Responses

| Condition | HTTP Status | Body |
|---|---|---|
| Missing `Authorization` header | `401 Unauthorized` | `{"detail": "Not authenticated"}` |
| Invalid or expired token | `401 Unauthorized` | `{"detail": "<Clerk error message>"}` |
| `CLERK_SECRET_KEY` not configured | `500 Internal Server Error` | (logged; generic error to client) |

---

## `UserContextMiddleware` Behaviour (Updated)

**Current behaviour** (before this feature):
- Extracts Bearer token from `Authorization` header
- Calls `verify_clerk_jwt(token)` — JWKS-based, JWTs only
- Sets `current_user_id_var` on success; returns 401 on failure

**New behaviour** (after this feature):
- Extracts Bearer token from `Authorization` header
- Calls `clerk_sdk.authenticate_request(httpx_req, AuthenticateRequestOptions(accepts_token=["session_token", "api_key"]))`
- On `is_signed_in == True`: extracts user ID via `to_auth()` and sets `current_user_id_var`
- On `is_signed_in == False`: returns 401 with `request_state.message`
- Calls `upsert_user(conn, clerk_id=user_id, email=email_or_none)` — same as current behaviour

---

## REST API Endpoints — Unchanged

The REST API (`/api/*`) continues to use `build_get_current_user()` which accepts **session JWTs only**. This function is not changed.

No new REST endpoints are added for API key management. Clerk handles key CRUD.

---

## Environment Variable Requirements

| Variable | Required | Description |
|---|---|---|
| `CLERK_SECRET_KEY` | Yes (new) | Used by `authenticate_request()` for both JWT (JWKS) and API key verification |
| `CLERK_JWKS_URL` | Yes (existing) | Retained for `build_get_current_user` JWT path |
| `CLERK_ISSUER` | Yes (existing) | Retained for `build_get_current_user` JWT path |

---

## Test Scenarios (Contract Tests)

These scenarios must be covered by `tests/contract/test_auth_contract.py`:

| ID | Scenario | Expected Result |
|---|---|---|
| T-MCP-01 | `/mcp` request with valid Clerk session JWT | `current_user_id_var` set; 200 from MCP layer |
| T-MCP-02 | `/mcp` request with valid Clerk API key (`ak_...`) | `current_user_id_var` set; 200 from MCP layer |
| T-MCP-03 | `/mcp` request with no Authorization header | 401 |
| T-MCP-04 | `/mcp` request with expired/invalid token | 401 |
| T-MCP-05 | `/mcp` request with malformed token (not JWT, not `ak_`) | 401 |
