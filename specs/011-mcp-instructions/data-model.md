# Data Model: MCP Server Connection Instructions & API Key Management

**Feature**: `011-mcp-instructions`
**Date**: 2026-02-27

---

## Entities

### API Key (Clerk-managed — NOT stored in Persona DB)

API keys are created, stored, and verified entirely by Clerk. Persona's backend never stores the plaintext secret and never issues key CRUD operations directly.

| Field | Type | Source | Notes |
|---|---|---|---|
| `id` | string | Clerk | Unique key identifier (e.g., `apk_2abc...`) |
| `secret` | string | Clerk | Plaintext secret (prefix `ak_`). **Only available in `create()` response. Never persisted.** |
| `name` | string | Clerk | Human-readable label (e.g., "My Claude Code key") |
| `subject` | string | Clerk | Owning entity ID — `user_2abc...` for user-scoped keys |
| `masked_preview` | string | Clerk | Last 4 chars + mask prefix (e.g., `ak_••••abcd`) |
| `created_at` | timestamp | Clerk | ISO-8601 creation time |
| `status` | enum | Clerk | `active` or `revoked` |
| `scopes` | string[] | Clerk | Granted scopes (empty list for unrestricted keys) |

**One active key per user** (FR-011): Enforced by the product rule that generating a new key automatically revokes any existing key for that user. This is configurable per Clerk dashboard settings.

**Persona never sees**: The plaintext `secret` after the initial `create()` response. The `<APIKeys />` component displays it once; after that only the masked preview is accessible.

---

### Auth Context (Runtime — not persisted)

When a request arrives at `/mcp`, the `UserContextMiddleware` resolves the auth context and sets `current_user_id_var` for MCP tool handlers.

| Field | Type | JWT path | API key path |
|---|---|---|---|
| `user_id` | string | `payload["sub"]` | `payload["subject"]` (or `to_auth().user_id`) |
| `email` | string? | `payload.get("email")` | `None` — not present in API key payload |
| `token_type` | enum | `session_token` | `api_key` |

**`upsert_user` call**: Both paths call `upsert_user(conn, clerk_id=user_id, email=email)`. When `email=None` (API key path), the existing row is looked up by `clerk_id`; no email update is made.

---

### User (existing Persona DB table — unchanged)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Internal Persona user PK |
| `clerk_id` | string | Clerk user ID (`user_2abc...`) — FK anchor for resumes, applications, accomplishments |
| `email` | string? | Populated from JWT auth; may be null for API key-only users |

No schema changes required for this feature.

---

## State Transitions

### API Key Lifecycle

```
[None] → create() → [Active, secret shown once]
                         ↓
                    [Active, masked]  ←→  show/hide toggle (session-local)
                         ↓
                    revoke() → [Revoked] → [None]
                         ↑
                    new create() auto-revokes previous key
```

### Frontend Snippet State

```
[No key pasted] → snippets show "YOUR_API_KEY" placeholder
[Key pasted in input] → snippets show real key (local state only)
[Input cleared] → snippets revert to placeholder
```

---

## No Schema Migrations Required

This feature makes no changes to the PostgreSQL schema. All API key state lives in Clerk's infrastructure.
