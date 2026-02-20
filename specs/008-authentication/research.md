# Research: Authentication and Multi-user Support

**Date**: 2026-02-18
**Feature**: 008-authentication

## Decision 1: Clerk + FastAPI Integration

**Decision**: Use `python-jose[cryptography]` for JWT validation with a custom FastAPI dependency.

**Rationale**: 
FastAPI's `HTTPBearer` security scheme is the idiomatic way to extract Bearer tokens. For validation, Clerk provides a JWKS (JSON Web Key Set) endpoint. Using `python-jose` allows us to:
1. Fetch and cache Clerk's public keys.
2. Verify the JWT signature against those keys.
3. Validate claims: `iss` (must match Clerk instance), `aud` (must match frontend origin or Clerk client ID), and `exp` (standard expiration).
4. Extract the `sub` claim as the `user_id`.

This approach is lightweight, doesn't rely on heavy generated SDKs, and integrates perfectly with FastAPI's dependency injection system.

**Alternatives considered**:
- `clerk-sdk-python`: The official SDK is still in early stages and often lags behind the JS/React SDKs. A manual JWT validation pattern is more robust and standard for FastAPI.
- `clerk-backend-api`: A generated SDK that provides full API coverage but is overkill for just validating JWTs.

## Decision 2: Clerk + React Integration

**Decision**: Use `@clerk/clerk-react` (v5+) with Vite's standard environment variable pattern.

**Rationale**:
The `@clerk/clerk-react` package is the official, well-maintained library for React applications. It provides:
- `ClerkProvider` for context management.
- `useAuth()` hook for accessing the JWT (`getToken()`) and session state.
- `useUser()` hook for accessing profile information.
- `SignedIn` / `SignedOut` / `RedirectToSignIn` components for declarative route protection.

Integration with Vite involves using `import.meta.env.VITE_CLERK_PUBLISHABLE_KEY`.

**Alternatives considered**:
- Vanilla `clerk-js`: Requires manual management of session state and token refreshing, which `@clerk/clerk-react` handles automatically.
- Custom Auth Provider: No reason to reinvent the wheel when Clerk provides a first-class React SDK.

## Decision 3: Secure Webhook Handling

**Decision**: Use the `svix` library to verify Clerk webhook signatures in a dedicated FastAPI POST endpoint.

**Rationale**:
Clerk uses Svix to sign webhooks. Verifying these signatures is critical to prevent spoofing. The `svix` Python library is the standard way to perform this verification.
- Endpoint: `POST /api/webhooks/clerk`
- Events: Handle `user.deleted` by performing a hard delete of all data associated with that `user_id`.

**Alternatives considered**:
- Manual HMAC verification: Error-prone and harder to maintain than using the recommended `svix` library.
- Unverified webhooks: Extremely insecure; allows anyone to trigger data deletion if they know the endpoint URL and a `user_id`.

## Decision 4: SQLite Migration (v3 → v4)

**Decision**: Create a dedicated `users` table (keyed by Clerk `sub`) as the FK anchor, then recreate `resume_version`, `application`, and `accomplishment` with `user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE`. Schema version advances from v3 to v4 via `migrate_v3_to_v4` in `migrations.py`.

**Rationale**:
- A dedicated `users` table enables proper referential integrity: `ON DELETE CASCADE` from `users` rows means a single `DELETE FROM users WHERE id = :sub` atomically hard-deletes all owned data (FR-008, FR-010) without needing application-level cleanup loops.
- SQLite does not support adding `NOT NULL` FK columns via `ALTER TABLE`. Table recreation (new table → copy → drop → rename) is the only correct path and is consistent with how v1→v2 was handled.
- Schema v3 is already occupied by the `accomplishment` table (feature 007-accomplishments). This migration must be v4.
- Pre-existing (single-user era) rows are assigned `user_id = 'legacy'`; a corresponding `users` row with `id = 'legacy'` is inserted to satisfy the FK constraint.

**Alternatives considered**:
- `ALTER TABLE` with nullable column: Would allow `NULL` user_ids to linger, weakening the invariant that every row is owned. Rejected.
- App-level cascade deletion: Requires iterating all owned tables in the webhook handler rather than a single SQL delete. More error-prone and violates the FK integrity model. Rejected.

## Decision 5: MCP Server Authentication

**Decision**: Validate `Authorization: Bearer <token>` in the FastMCP/FastAPI layer for SSE transport.

**Rationale**:
When the MCP server is mounted inside FastAPI (via `app.mount("/mcp", mcp_app)`), it inherits the ability to use FastAPI dependencies or middleware.
For tool handlers:
- We will implement a wrapper or use a context variable to access the `user_id` extracted from the JWT.
- For local `stdio` usage, we will allow an optional `--token` flag or environment variable to simulate the authenticated user, as `stdio` doesn't have HTTP headers.

**Alternatives considered**:
- API Keys for MCP: Adds management overhead. Reusing the Clerk JWT is more consistent with the frontend's auth state.
- No Auth for MCP: Violates the multi-user requirement.

## Decision 6: Passing User Context to MCP Tools

**Decision**: Use Python's `contextvars` to manage user identity across the FastAPI and FastMCP layers.

**Rationale**: 
FastMCP tools are standard Python functions. When the MCP server is mounted in FastAPI, requests pass through FastAPI's middleware stack. We will:
1. Implement a FastAPI dependency/middleware that validates the Clerk JWT.
2. Use a `ContextVar[str]` to store the extracted `user_id` for the duration of the request.
3. In the MCP tool handlers, access this `ContextVar` to filter database queries by the current user.
4. For `--stdio` transport (local usage), we will provide a way to set this context (e.g., an environment variable `PERSONA_USER_ID`) to ensure tools remain functional during local development.

**Alternatives considered**:
- Passing `user_id` as a tool argument: Leaks internal state to the LLM and complicates tool signatures.
- Custom MCP headers: Not standard across all MCP clients.

## Decision 7: JWKS Caching Strategy

**Decision**: Implement a simple in-memory cache for Clerk's JWKS with a 1-hour TTL and "on-demand" refresh.

**Rationale**:
Clerk's public keys change infrequently. Fetching them on every request would add significant latency and unnecessary load on Clerk's API.
- **Cache**: A global dictionary or singleton object.
- **Expiration**: Keys are considered valid for 1 hour.
- **Refresh**: If a JWT arrives with a `kid` (Key ID) not present in the cache, the backend will attempt to fetch a fresh JWKS before failing validation. This handles key rotation gracefully.

**Alternatives considered**:
- Redis/External Cache: Overkill for a single-instance SQLite-backed server.
- Permanent Caching: Insecure, as it would fail when Clerk rotates keys.
