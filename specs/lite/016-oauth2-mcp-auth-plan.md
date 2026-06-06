# Plan 016 - OAuth2 MCP Server Auth (drop API keys)

Date: 2026-05-25

Replace MCP API-key/dual-auth with standard OAuth2. MCP client points at URL only; unauth req → 401 + `WWW-Authenticate` → Protected Resource Metadata at `/.well-known/oauth-protected-resource/mcp`. Clerk = OAuth2 authorization server (Dynamic Client Registration). Server = resource server: validate tokens, no key config.


## Requirements

### R1 - Server as OAuth2 resource server

`/mcp` accepts only Clerk-issued OAuth2 bearer access tokens. No API keys, no key paste.

* Unauth `/mcp` req → `401` with header `WWW-Authenticate: Bearer resource_metadata="<public-url>/.well-known/oauth-protected-resource/mcp"`.
* `GET /.well-known/oauth-protected-resource/mcp` → `200` RFC 9728 JSON: `resource`, `authorization_servers` (Clerk issuer).
* Valid token (sig via Clerk JWKS, issuer match, not expired, aud = MCP resource URL) → tool call proceeds, user-scoped.
* Bad token (expired / wrong issuer / wrong aud / bad sig) → `401`.
* Tool handlers still resolve user via `require_user_id()` — `current_user_id_var` set from token `sub` per call.
* Well-known route registered before SPA static catch-all (not shadowed).

### R2 - Enforce audience binding (RFC 8707)

Access token `aud` must equal canonical MCP resource URL (`<public-url>/mcp`).

* `JWTVerifier(audience=<resource-url>)` rejects tokens not bound to this resource.
* Resource URL derived from new `PERSONA_PUBLIC_URL` config.
* Manual Clerk step verifies Clerk mints resource-bound tokens (resource indicator passthrough).

### R3 - Remove API-key / dual-auth code

Delete Clerk-SDK dual-auth path; OAuth only.

* Remove `build_clerk_client`, `authenticate_mcp_request`, `extract_user_id_from_request_state` from `auth.py` + the `/mcp` branch in `UserContextMiddleware`.
* Remove `resolve_clerk_secret_key` startup-validation call if `CLERK_SECRET_KEY` unused after (grep-guard; webhook secret is separate).
* REST API JWT path (`build_get_current_user`, `verify_clerk_jwt`) unchanged.
* stdio mode unchanged (`PERSONA_USER_ID`); no token there.

### R4 - Clean up home-page connect UI

Drop key-gen + key-paste. MCP client just points at URL; client runs OAuth.

* Remove `APIKeys` Clerk component + `APIKeysErrorBoundary` + paste-key step.
* Snippets carry no `Authorization` header: `claude mcp add --transport http persona <URL>`; Cursor/Copilot/Kiro JSON = bare `url`, no `headers`.
* Copy explains: client opens browser to sign in (OAuth), no key to manage.
* Remove now-dead CSS (`apiKeysDisabled`, `pasteRow`, `pasteInput`, `pasteHint`, step 01/02 chrome).

### R5 - Config + deploy

New public-URL config wired through compose/README.

* `PERSONA_PUBLIC_URL` (externally reachable base, e.g. `https://persona.example.com`) — required in prod, used for resource URL + metadata `base_url`.
* docker-compose passes it; README documents it + the no-key connect flow.
* Manual Clerk setup steps documented (see Tasks P0, flagged HUMAN).


## Design

### Lib choice — FastMCP native (2.14.5 installed)

FastMCP ships `RemoteAuthProvider` + `JWTVerifier` (`fastmcp.server.auth`). Pass `auth=provider` to `FastMCP(...)` → `http_app()` auto-serves RFC 9728 metadata route + emits `WWW-Authenticate` on 401 via its `AuthenticationMiddleware`. No hand-rolled metadata/401. Clerk supports DCR → resource-server-only mode (no `OAuthProxy`).

```python
# auth.py — new
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier

def build_mcp_auth() -> RemoteAuthProvider:
    public = resolve_public_url()              # e.g. https://persona.example.com
    resource = f"{public}/mcp"                 # RFC 8707 canonical resource
    verifier = JWTVerifier(
        jwks_uri=resolve_clerk_jwks_url(),
        issuer=resolve_clerk_issuer(),
        audience=resource,                      # R2 aud binding
        base_url=public,
    )
    return RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[resolve_clerk_issuer()],
        base_url=public,
        resource_name="Persona",
    )
```

```python
# server.py — wire at construction
mcp = FastMCP("persona", auth=build_mcp_auth())
```

### user_id bridge (keep tools unchanged)

FastMCP validates token + stores `AccessToken` in its ctx. Tools call `require_user_id()` → reads `current_user_id_var`. Bridge via FastMCP middleware (`fastmcp.server.middleware.Middleware`) `on_call_tool`: read `get_access_token()`, pull `sub` from claims, `set` contextvar for the call, `upsert_user`, reset after.

```python
# tools middleware
class UserContextToolMiddleware(Middleware):
    async def on_call_tool(self, ctx, call_next):
        tok = get_access_token()               # fastmcp.server.dependencies
        sub = (tok.claims or {}).get("sub") if tok else None
        reset = current_user_id_var.set(sub)
        try:
            if sub and _conn: upsert_user(_conn, sub, None, None)
            return await call_next(ctx)
        finally:
            current_user_id_var.reset(reset)
mcp.add_middleware(UserContextToolMiddleware())
```

Removes `/mcp` upsert+contextvar logic from Starlette `UserContextMiddleware`. That middleware keeps only: REST JWT contextvar (non-/mcp), stdio `PERSONA_USER_ID`.

### Metadata route ordering

`server.py` already appends `mcp_app.routes` to FastAPI router *before* SPA static mount (`server.py:332`). RFC 9728 route lives in `mcp_app.routes` → included + ahead of catch-all. No change needed; add test to lock it.

### Flow (client POV)

```
client → POST /mcp (no token)
server → 401 WWW-Authenticate: Bearer resource_metadata="…/.well-known/oauth-protected-resource/mcp"
client → GET that metadata → authorization_servers=[clerk-issuer]
client → GET <clerk>/.well-known/oauth-authorization-server (RFC 8414)
client → DCR register (RFC 7591) @ clerk
client → PKCE authorize (browser) → token (aud=<url>/mcp)
client → POST /mcp Bearer <token> → JWTVerifier OK → tool runs
```

### Two JWKS validators — accepted

REST keeps `verify_clerk_jwt` (jose); MCP uses `JWTVerifier` (fastmcp). Minor dup, both hit same Clerk JWKS. Share later if it bites; not this plan.


## Tasks

### P0 - Clerk manual setup (HUMAN STEPS)

Phase = human actions in Clerk Dashboard. Not code. Verify before P1 ships.

- [ ] T01 **HUMAN**: Enable Dynamic Client Registration in Clerk (OAuth Applications / OAuth2 server settings). Confirm `https://<frontend-api>/.well-known/oauth-authorization-server` advertises `registration_endpoint` + `code_challenge_methods_supported` (PKCE).
- [ ] T02 **HUMAN**: Confirm Clerk allows DCR loopback/dynamic redirect URIs (CLI clients use `http://localhost:<port>/callback`).
- [ ] T03 **HUMAN**: Confirm Clerk honors `resource` indicator → mints access tokens with `aud=<public-url>/mcp` (needed for R2). If unsupported, fall back to R2 "skip aud" + flag.
- [ ] T04 **HUMAN**: Set `PERSONA_PUBLIC_URL` + existing Clerk envs in deploy env/secrets.

### P1 - Backend auth swap

- [x] T05 Add `resolve_public_url()` (`PERSONA_PUBLIC_URL`, required-in-prod) to `config.py`.
- [x] T06 Add `build_mcp_auth()` (RemoteAuthProvider + JWTVerifier, aud binding) to `auth.py`.
- [x] T07 `FastMCP("persona", auth=build_mcp_auth())` in `server.py`; conditional so test-injected (non-prod) path can skip/stub auth.
- [x] T08 Add `UserContextToolMiddleware` (get_access_token → contextvar + upsert); `mcp.add_middleware(...)`.
- [x] T09 Strip `/mcp` branch from Starlette `UserContextMiddleware`; keep REST + stdio branches.

### P2 - Remove dead auth code

- [x] T10 Delete `build_clerk_client`, `authenticate_mcp_request`, `extract_user_id_from_request_state` from `auth.py` + now-unused imports (`Clerk`, SDK types).
- [x] T11 Grep `CLERK_SECRET_KEY`/`resolve_clerk_secret_key`; remove startup validation + config fn if unused after T10 (keep webhook secret).

### P3 - Frontend connect cleanup

- [x] T12 `pages/home/index.tsx`: remove `APIKeys`, `APIKeysErrorBoundary`, paste-key state/step; collapse to single "Add to your assistant" step; update snippets (no `Authorization` header / `headers`); update copy (browser OAuth, no key).
- [x] T13 `HomeView.module.css`: delete dead key-UI classes.

### P4 - Config/docs

- [x] T14 docker-compose: add `PERSONA_PUBLIC_URL`. README: document var + new keyless OAuth connect flow + link manual Clerk steps.

### P5 - Tests

- [x] T15 Contract: `GET /.well-known/oauth-protected-resource/mcp` → 200, body has `resource` + `authorization_servers`.
- [x] T16 Contract: unauth `POST /mcp` → 401 + `WWW-Authenticate` header references metadata URL.
- [x] T17 Contract: valid mock JWT (right aud/issuer) → tool ok; wrong aud → 401; expired → 401.
- [x] T18 Update/remove `test_auth.py` + `test_auth_contract.py` API-key/dual-auth cases (now gone).
- [x] T19 Test well-known route not shadowed by SPA catch-all (resolves before static).


### Implementation Notes

- Sequence: P0 (human, gate) → P1 → P2 → (P3 ∥ P4) → P5. P0 must verify before MCP usable end-to-end.
- JWTVerifier mock in tests: reuse RSA keypair helpers in `test_auth_contract.py` (`_gen_rsa_key_pair`, `_make_token`); point `jwks_uri` at a stub or inject `public_key=`.
- `get_access_token` import: `from fastmcp.server.dependencies import get_access_token`. `Middleware` base: `from fastmcp.server.middleware import Middleware`.
- Audience risk: R2 depends on Clerk resource-indicator support (T03). If Clerk can't bind aud, drop `audience=` (issuer+sig+exp only) + note follow-up — do NOT block ship on it.
- Test-mode bypass: `create_app(service=...)` injects pre-built service = non-prod; gate auth wiring same as existing `_production_mode` so cross-interface tests keep passing without real Clerk.
- `RemoteAuthProvider` serves only the *protected-resource* metadata; AS metadata + DCR + token endpoints live on Clerk. Server never proxies them (resource-server-only).
- No DB/schema change. No new deps (fastmcp already 2.14.5).
- Manual Clerk steps (P0) tagged **HUMAN** per roadmap — do not attempt in code.
