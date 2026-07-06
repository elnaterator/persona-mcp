# Plan 017 - OAuth DCR loopback proxy (FastMCP OAuthProxy)

Date: 2026-07-05

Native MCP clients (Claude Desktop, Cursor, VS Code) register one loopback redirect
(`http://localhost:PORT/callback`) but send the other (`http://127.0.0.1:PORT/callback`);
per OAuth these are distinct strings, so Clerk's `redirect_uri` validation rejects the
authorize call. Fix: replace `RemoteAuthProvider` with FastMCP's `OAuthProxy` — the server
handles DCR locally (loopback `localhost`/`127.0.0.1` patterns allowed by default),
proxies authorize/token to Clerk through one fixed pre-registered redirect URI, and
issues its own reference JWTs to clients.

> **Roadmap correction.** The roadmap says "adopt Clerk's `mcp-tools` proxy". Researched
> `clerk/mcp-tools` (README, `server.ts`, full PR history): it ships TypeScript *client*
> helpers and RFC 9728/8414 metadata generators only — there is no server-side DCR/loopback
> proxy in that repo, and it is Node-only anyway. FastMCP's `OAuthProxy`
> (`fastmcp.server.auth.oauth_proxy`, already installed at 2.14.5) implements exactly the
> described behavior — local DCR, loopback redirect expansion, `redirect_uri` normalization
> on authorize + token, `token_endpoint_auth_method` override — natively in Python with
> zero new dependencies. Bonus: clients no longer register with Clerk at all, which also
> insulates us from the Nov 2025 DCR → CIMD spec shift.

## Requirements

### R1 - OAuthProxy replaces RemoteAuthProvider

`/mcp` auth becomes a DCR-compliant proxy in front of Clerk; loopback mismatch gone.

* Unauth `POST /mcp` → `401` + `WWW-Authenticate` referencing
  `/.well-known/oauth-protected-resource/mcp` (unchanged from 016).
* Protected-resource metadata now lists **our own** base URL as the authorization server;
  proxy serves `/.well-known/oauth-authorization-server`, `/register`, `/authorize`,
  `/token` on our domain (routes come from `mcp_app`, registered before SPA catch-all).
* `POST /register` accepts any client with a loopback redirect; both
  `http://localhost:*` and `http://127.0.0.1:*` accepted (FastMCP default
  `allowed_client_redirect_uris=None` = localhost-only patterns).
* `/authorize` forwards to Clerk using the fixed `<PERSONA_PUBLIC_URL>/auth/callback`;
  after Clerk redirects back, the proxy exchanges the code server-side and redirects to
  the client's own loopback URI with a proxy-issued code.
* Client presents proxy-issued JWT; token-swap validation (below) passes → tool call
  proceeds user-scoped. Garbage/expired token → 401.

### R2 - Clerk static OAuth app replaces DCR dependency

One pre-registered confidential client in Clerk; MCP clients never touch Clerk DCR.

* **HUMAN**: create an OAuth application in Clerk Dashboard with redirect URI
  `<PERSONA_PUBLIC_URL>/auth/callback`; capture client id/secret.
* New env vars `CLERK_OAUTH_CLIENT_ID` / `CLERK_OAUTH_CLIENT_SECRET`, required in
  production mode alongside existing `PERSONA_PUBLIC_URL`/`CLERK_ISSUER`/`CLERK_JWKS_URL`.
* Upstream endpoints derived from issuer: `<issuer>/oauth/authorize`,
  `<issuer>/oauth/token` — confirmed against `<issuer>/.well-known/oauth-authorization-server`
  during T02 (HUMAN check; adjust config if Clerk paths differ).
* **HUMAN (optional)**: after ship, disable Dynamic Client Registration in Clerk.

### R3 - User identity bridge unchanged

Tools keep resolving the Clerk user id per call.

* `OAuthProxy.load_access_token` verifies the proxy JWT, looks up the stored upstream
  Clerk token, and validates it through our `token_verifier` — the returned `AccessToken`
  claims are the *Clerk* claims, so `UserContextToolMiddleware` still reads `sub` and
  upserts the user. Verify with a contract test; adjust claim extraction only if proven
  necessary.
* Existing `_DiagnosticJWTVerifier` (JWKS + issuer strict, `audience=None`) is reused as
  the proxy's `token_verifier`.
* stdio mode (`PERSONA_USER_ID`) untouched.

### R4 - State, config, docs

* Proxy state (client registrations, encrypted upstream tokens) uses FastMCP's default
  encrypted DiskStore — persist it in Docker via a volume so server restarts don't force
  re-auth; document the path.
* docker-compose + README: new env vars, volume, updated connect-flow description
  (client → our AS metadata → local register → browser consent → Clerk sign-in).
* Home page copy stays URL-only; adjust wording only if it references Clerk sign-in
  specifics that changed.

### R5 - Tests updated

* Contract: protected-resource metadata `authorization_servers == [<public-url>]`.
* Contract: AS metadata endpoint serves `registration_endpoint`, `authorization_endpoint`,
  `token_endpoint` on our domain.
* Contract: `POST /register` with `redirect_uris=["http://127.0.0.1:33418/callback"]`
  → 201; same for `localhost` variant.
* Contract: unauth `/mcp` → 401 + `WWW-Authenticate` (update expected metadata URL if
  changed); invalid bearer → 401.
* Update/remove 016 tests asserting Clerk as the advertised authorization server.
* Test-mode gate: non-prod `create_app(service=...)` still runs authless.

## Design

```python
# auth.py
from fastmcp.server.auth.oauth_proxy import OAuthProxy

def build_mcp_auth() -> OAuthProxy:
    public = resolve_public_url()
    issuer = resolve_clerk_issuer()
    verifier = _DiagnosticJWTVerifier(
        jwks_uri=resolve_clerk_jwks_url(),
        issuer=issuer,
        audience=None,
        base_url=public,
    )
    return OAuthProxy(
        upstream_authorization_endpoint=f"{issuer}/oauth/authorize",
        upstream_token_endpoint=f"{issuer}/oauth/token",
        upstream_client_id=resolve_clerk_oauth_client_id(),
        upstream_client_secret=resolve_clerk_oauth_client_secret(),
        token_verifier=verifier,
        base_url=public,
        redirect_path="/auth/callback",
        # allowed_client_redirect_uris=None → localhost + 127.0.0.1 defaults
    )
```

Flow (client POV):

```
client → POST /mcp (no token) → 401 + resource metadata
client → GET /.well-known/oauth-protected-resource/mcp → authorization_servers=[<public-url>]
client → GET <public-url>/.well-known/oauth-authorization-server
client → POST <public-url>/register (loopback redirect, either variant) → creds
client → GET <public-url>/authorize (PKCE) → consent page → Clerk sign-in
clerk  → GET <public-url>/auth/callback → proxy swaps code, stores Clerk tokens encrypted
proxy  → redirect to client loopback URI with proxy code
client → POST <public-url>/token → FastMCP reference JWT
client → POST /mcp Bearer <jwt> → token swap → Clerk claims → tool runs
```

Token model: client holds a FastMCP-signed reference JWT (`jti`); the Clerk access/refresh
tokens live encrypted server-side. Every `/mcp` call re-validates the stored Clerk token
via JWKS, so revocation at Clerk takes effect. `jwt_signing_key` defaults to a key derived
from the upstream client secret — no extra config needed.

Wiring in `server.py` is unchanged: `build_mcp_auth()` return type widens to
`OAuthProxy`, still passed as `FastMCP("persona", auth=...)` under `_production_mode`.

## Tasks

### P0 - Clerk manual setup (HUMAN STEPS)

- [ ] T01 **HUMAN**: Create OAuth application in Clerk Dashboard, redirect URI
      `<PERSONA_PUBLIC_URL>/auth/callback`; record client id/secret into deploy env.
- [ ] T02 **HUMAN**: `GET <issuer>/.well-known/oauth-authorization-server` — confirm
      `authorization_endpoint`/`token_endpoint` match `<issuer>/oauth/authorize|token`.

### P1 - Backend proxy swap

- [x] T03 `config.py`: add `resolve_clerk_oauth_client_id()` /
      `resolve_clerk_oauth_client_secret()` (required in prod).
- [x] T04 `auth.py`: rewrite `build_mcp_auth()` → `OAuthProxy` per Design; keep
      `_DiagnosticJWTVerifier` as `token_verifier`. Pass explicit
      `allowed_client_redirect_uris=DEFAULT_LOCALHOST_PATTERNS` — `None` means
      allow-all, not localhost-only (FastMCP constructor docstring is misleading);
      the explicit patterns are what enable the loopback-variant tolerance.
- [x] T05 `UserContextToolMiddleware` unchanged: `load_access_token` returns the
      `token_verifier`'s AccessToken (Clerk claims), so the `sub` bridge still works.
      Middleware half already covered by `test_mcp_user_scoping.py`; real-token swap
      covered by T11 (needs live Clerk).

### P2 - Config/deploy/docs

- [x] T06 docker-compose: new `CLERK_OAUTH_CLIENT_ID`/`_SECRET`, `FASTMCP_HOME` +
      `mcp-oauth-state` volume for proxy state. README + `.env.example`: documented
      vars, volume, and the new proxy connect flow + Clerk setup steps.

### P3 - Tests

- [x] T07 Contract: protected-resource metadata advertises `<public-url>` as AS (not
      Clerk); AS metadata endpoint live with register/authorize/token endpoints on
      our domain.
- [x] T08 Contract: `/register` accepts both `127.0.0.1` and `localhost` loopback
      redirects; `/authorize` tolerates the loopback host mismatch (302) and rejects
      an unregistered non-loopback redirect (400). (Register itself is permissive per
      DCR; the redirect constraint is enforced at authorize — plan updated to match.)
- [x] T09 Contract: raw Clerk-style JWT and garbage tokens are rejected (401) — proxy
      requires its own reference JWTs. Positive token-swap path deferred to T11
      (seeding FastMCP's private token stores would couple the test to internals).
- [x] T10 Replaced 016 contract tests (Clerk-as-AS → us-as-AS, token semantics) and
      kept the SPA catch-all shadowing test green with the new well-known routes.

### P4 - Verify end-to-end

- [ ] T11 **Manual (needs live Clerk + deployed instance)**: connect from Claude
      Desktop or Cursor with the loopback `127.0.0.1` variant; confirm sign-in + tool
      call. Loopback fix is verified at the HTTP layer here (register 127.0.0.1 →
      authorize localhost → 302, no redirect_uri 400).

### Implementation Notes

- Sequence: P0 gates real-world verification only; P1 → (P2 ∥ P3) → T11. Code work can
  proceed before P0 with test doubles.
- No new dependencies: fastmcp 2.14.5 already ships `OAuthProxy` + storage/crypto deps.
- Consent screen: `require_authorization_consent=True` (default) shows a FastMCP consent
  page before Clerk sign-in — keep it (MCP security best practice).
- Proxy state store: default encrypted DiskStore under the FastMCP data dir; if the
  Docker volume is awkward, switch `client_storage` to a Postgres-backed `AsyncKeyValue`
  in a follow-up — not this plan.
- Token lifetime: Clerk `expires_in` drives proxy JWT expiry; refresh handled by proxy
  against `<issuer>/oauth/token`. No config needed unless Clerk omits `expires_in`
  (then set `fallback_access_token_expiry_seconds`).
- `token_endpoint_auth_method`: leave `None` (authlib default `client_secret_basic`);
  set `"client_secret_post"` only if Clerk rejects basic auth during T11.
- CIMD watch item stands: proxy removes Clerk-DCR coupling now; revisit client-side CIMD
  once target clients (Claude/Cursor/VS Code) actually ship it.
