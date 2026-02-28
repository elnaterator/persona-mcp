# Phase 0 Research: MCP Server Connection Instructions & API Key Management

**Feature**: `011-mcp-instructions`
**Date**: 2026-02-27
**Status**: Complete

---

## Decision 1: API Key Verification Backend Strategy

**Decision**: Use `clerk-backend-api` Python SDK's `authenticate_request()` for all token verification at the `/mcp` endpoint, supporting both session JWTs and native API keys via `accepts_token=["session_token", "api_key"]`.

**Rationale**: Clerk native API keys are opaque tokens (prefix `ak_`) and cannot be verified via JWKS. The `clerk-backend-api` SDK handles both token types in a single call: JWTs are verified locally (or via JWKS) using `CLERK_SECRET_KEY`; API keys are verified via a network call to Clerk's backend. This avoids maintaining two separate verification code paths.

**Alternatives considered**:
- Manual JWKS + custom hash-based tokens: More code, requires a new DB table for key storage, requires a `/api/keys` REST API. Rejected in favour of Clerk's managed approach.
- `python-jose` for JWTs only: Already in use but cannot verify opaque API key tokens at all.

**Key implementation detail**: `authenticate_request()` expects an `httpx.Request` object. FastAPI's `Request` must be wrapped:
```python
httpx_req = httpx.Request(method=req.method, url=str(req.url), headers=dict(req.headers))
```

---

## Decision 2: User ID Extraction (JWT vs API Key Paths)

**Decision**: Use `request_state.to_auth()` uniformly; extract `.user_id` for API keys and `.sub` for session tokens. Normalise to a single `user_id` string before calling `upsert_user`.

**Rationale**: The `to_auth()` method returns `SessionAuthObjectV2` for JWTs (`.sub` is the Clerk user ID) and `APIKeyMachineAuthObject` for API keys (`.user_id` if subject starts with `user_`). The `APIKeyMachineAuthObject` does not include an `email` claim — for machine callers this is expected; `upsert_user` will be called with `email=None` on the API key path.

**Key difference**:

| Token type | `payload` field | `to_auth()` field |
|---|---|---|
| Session JWT | `payload["sub"]` | `auth.sub` |
| Native API key | `payload["subject"]` | `auth.user_id` |

Both produce a `user_2abc...` format Clerk user ID when the key is user-scoped.

---

## Decision 3: Scope of `UserContextMiddleware` vs `build_get_current_user`

**Decision**: Only `UserContextMiddleware` (used by the `/mcp` MCP endpoint) is updated to accept both JWT and API keys. `build_get_current_user` (FastAPI REST API dependency) remains JWT-only and is unchanged.

**Rationale**: MCP tools are the machine-facing surface area that API keys are designed to access. The REST API (`/api/*`) is accessed by the frontend with Clerk session JWTs only. Extending REST API auth to accept API keys is out of scope for this feature (FR-010 targets `/mcp` only).

---

## Decision 4: Required Environment Variables

**Decision**: Add `CLERK_SECRET_KEY` as a required backend env var. `CLERK_JWKS_URL` and `CLERK_ISSUER` remain (used by `build_get_current_user` for JWT-only REST API auth) but are not needed by the new `UserContextMiddleware` path.

**Variables**:

| Variable | Required by | Notes |
|---|---|---|
| `CLERK_SECRET_KEY` | `UserContextMiddleware` (new) | Starts with `sk_test_` or `sk_live_`. Never expose to frontend. |
| `CLERK_JWKS_URL` | `build_get_current_user` (existing) | Remains for REST API JWT verification |
| `CLERK_ISSUER` | `build_get_current_user` (existing) | Remains for REST API JWT verification |
| `VITE_CLERK_PUBLISHABLE_KEY` | Frontend (existing) | Clerk React SDK initialisation |
| `VITE_MCP_SERVER_URL` | Frontend (new) | Build-time env var for MCP server URL in config snippets |

---

## Decision 5: Frontend Key Management UI — `<APIKeys />` Component Limitations

**Decision**: Use Clerk's `<APIKeys />` React component for key lifecycle (generate, revoke). For config snippet substitution, add a separate user-controlled "paste your API key" text input that drives real-time token substitution in the displayed config commands.

**Rationale**: The `<APIKeys />` component has NO creation callbacks — `APIKeyResource.secret` is only available ephemerally inside the component's own create flow. There is no `useAPIKeys` hook or `onKeyCreate` callback in `@clerk/clerk-react`. The component renders its own UI (key display, masking, revocation). Config snippets therefore cannot auto-populate from the component's state.

**UX flow**:
1. User sees `<APIKeys />` component — generates/manages keys there.
2. Below the component, a text input prompts: "Paste your API key to populate config commands."
3. Typing in the input immediately substitutes the key into all displayed config snippets (local state only, never sent to server).
4. Snippets default to a visible placeholder (`YOUR_API_KEY`) until the user pastes.

**FR-004/FR-005 compliance**: The `<APIKeys />` component handles unmasked one-time display (FR-004) and masked subsequent display (FR-005) out of the box.

**Implementation caveat — import path**: Official docs use `@clerk/nextjs` import paths. Whether `<APIKeys />` is exported from `@clerk/clerk-react` is not confirmed in current docs (feature is in public beta, React-specific docs may lag). At implementation time, verify the export exists in `@clerk/clerk-react`; if not, the fallback is `useClerk().apiKeys.create()` (see Alternative below).

**Alternative if `<APIKeys />` unavailable in `@clerk/clerk-react`**: Build a lightweight custom UI using `useClerk()` — `clerk.apiKeys.create()` returns the secret directly in the promise. This gives the app code control over one-time display and eliminates the need for the "paste your key" input workaround. This is in scope as a fallback only; the `<APIKeys />` component remains the preferred approach per the spec assumption.

---

## Decision 6: MCP Config Formats for Supported Assistants

All four assistants use streamable-HTTP transport with an `Authorization: Bearer <KEY>` header.

### Claude Code (Anthropic CLI)

**Config method 1 — CLI command (preferred):**
```bash
claude mcp add --transport http persona https://your-persona-server.com/mcp \
  --header "Authorization: Bearer YOUR_API_KEY"
```

**Config method 2 — JSON config** (`~/.claude.json` or project `.mcp.json`):
```json
{
  "mcpServers": {
    "persona": {
      "type": "http",
      "url": "https://your-persona-server.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### Cursor

**Config file**: `.cursor/mcp.json` (project-level) or `~/.cursor/mcp.json` (global)

```json
{
  "mcpServers": {
    "persona": {
      "url": "https://your-persona-server.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### GitHub Copilot (VS Code)

**Config file**: `.vscode/mcp.json` (workspace-level) or user settings via command palette

Note: VS Code/Copilot uses `"servers"` as the top-level key (not `"mcpServers"`).

```json
{
  "servers": {
    "persona": {
      "type": "http",
      "url": "https://your-persona-server.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### Amazon Kiro

**Config file**: `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "persona": {
      "url": "https://your-persona-server.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

---

## Decision 7: FR-009 Disposition

**Decision**: FR-009 ("The backend MUST provide authenticated API endpoints to: create an API key, revoke/regenerate, and retrieve key status") is superseded by the Clerk `<APIKeys />` component approach and does NOT require implementation.

**Rationale**: Clerk's native API key management (creation, revocation, masking, one-time reveal) is fully handled server-side by Clerk and surface-side by the `<APIKeys />` React component. No custom backend REST endpoints for key CRUD are needed. The only backend change is teaching `UserContextMiddleware` to accept opaque `ak_` tokens for MCP auth.

---

## Decision 8: `clerk-backend-api` Dependency Justification (Constitution IV)

**Constitution Principle IV** requires every third-party dependency to justify its inclusion.

**Justification**: Clerk native API keys are opaque tokens that cannot be verified via public-key cryptography (JWKS). The only supported verification method is a network call to Clerk's `/api_keys/verify` endpoint. `clerk-backend-api` is the official Clerk Python SDK that implements this endpoint call, along with unified `authenticate_request()` that handles both session JWTs and API keys. No Python standard library or already-included library provides this capability. The dependency is maintained by Clerk (the same vendor as the auth layer already in use), MIT-compatible license, and has minimal transitive dependencies.

**`python-jose[cryptography]` retained?**: Yes — `build_get_current_user` (REST API dependency) continues to use the existing JWKS-based JWT verification. These paths are independent. Future work could unify them.
