# Plan 025 - Close MCP 2025-11-25 authorization spec gaps (CIMD, audience, root PRM)

Date: 2026-08-22

The Nov 2025 MCP authorization spec makes Client ID Metadata Documents (CIMD) the
preferred client-identification mechanism and demotes DCR to backwards compatibility.
Our proxy (FastMCP 2.14.5) had no CIMD code, advertised no
`client_id_metadata_document_supported`, and never validated token audience. Upgrade
to FastMCP 3.4.7 — which ships CIMD and audience-bound proxy tokens — and close the
remaining discovery gap ourselves.

## Requirements

### R1 - CIMD client identification

Clients that identify with an HTTPS URL `client_id` (hosting their own metadata
document) can authorize without registering.

* AS metadata at `/.well-known/oauth-authorization-server` advertises
  `client_id_metadata_document_supported: true`.
* `token_endpoint_auth_methods_supported` includes `none` and `private_key_jwt` —
  CIMD clients hold no shared secret.
* A URL-shaped `client_id` routes to the CIMD fetch path; an opaque DCR id does not.
* `registration_endpoint` stays advertised: DCR remains for pre-CIMD clients.
* CIMD is wired explicitly (`enable_cimd=True`), not inherited from a library default.

### R2 - Token audience binding

The server only accepts tokens minted for it (spec MUST; previously `audience=None`).

* Proxy-issued client JWTs carry `aud = <PKTX_PUBLIC_URL>/mcp`.
* A token with the same signing key but a foreign `aud` is rejected.
* Upstream Clerk tokens stay signature+issuer-verified only, documented as such:
  there we are the OAuth client, not the resource.

### R3 - Root protected-resource metadata

Clients that skip the `WWW-Authenticate` hint and probe the root well-known path get
metadata instead of the SPA 404.

* `GET /.well-known/oauth-protected-resource` returns 200.
* Root and `/mcp`-suffixed documents are byte-identical (same handler).
* Alias is registered before the static catch-all mount.

### R4 - Hosted client redirect URIs

A hosted MCP client (CIMD document pointing at an HTTPS callback) can be allowed
without loosening loopback handling.

* `PKTX_EXTRA_CLIENT_REDIRECT_URIS` (comma-separated patterns) extends the allowlist.
* Unset/blank = loopback only; a hosted redirect is rejected by default.
* Same allowlist gates DCR and CIMD clients.

## Design

FastMCP 3.4.7 does the heavy lifting:

* `OAuthProxy(enable_cimd=True)` → `CIMDClientManager` (SSRF-guarded fetch, `client_id`
  == URL check, redirect validation against our allowlist, HTTP-cache-respecting).
* `set_mcp_path()` builds a `JWTIssuer` with `audience=<resource_url>`; `verify_token`
  rejects a mismatched `aud`. Signing key derives deterministically from
  `upstream_client_secret`, so it stays stable across Lambda instances — no new env.

What stays ours: the root PRM alias (`server._add_root_resource_metadata_alias` reuses
the FastMCP handler at a second path) and the redirect allowlist env.

Deliberately not done: **scopes**. `scopes_supported` stays `[]` and the 401 challenge
carries no `scope`. The server has no scope model — a token is all-or-nothing for one
user's data — and inventing one means Clerk-side configuration for no security gain.
Spec-wise `scope` is SHOULD, and an empty `scopes_supported` correctly says "no scopes
required".

Upgrade fallout was small: `key_value.shared.utils.managed_entry` →
`key_value.aio._utils.managed_entry`, and test helpers reaching into the removed
`mcp._tool_manager._tools` now use the public `await mcp.list_tools()`.

## Tasks

### P1 - Upgrade

- [x] T01 Bump `fastmcp>=3.4.7`, `uv lock`, `uv sync`.
- [x] T02 Fix `ManagedEntry` import path in `oauth_store.py`.
- [x] T03 Move test tool-lookup helpers to `mcp.list_tools()` (6 files).

### P2 - Spec gaps

- [x] T04 `enable_cimd=True` + allowlist composition in `auth.build_mcp_auth`.
- [x] T05 `config.resolve_extra_client_redirect_uris()`.
- [x] T06 Root PRM alias in `server.py`, registered before the static mount.
- [x] T07 Docstrings: audience is now enforced at the client-facing boundary.

### P3 - Tests + docs

- [x] T08 Contract: CIMD advertisement, secretless auth methods, DCR still offered,
      URL vs opaque client id.
- [x] T09 Contract: issuer audience == resource URL, foreign-aud token rejected,
      own token accepted.
- [x] T10 Contract: root PRM alias 200 + identical document.
- [x] T11 Contract: hosted redirect rejected by default, accepted when configured.
- [x] T12 Unit: `PKTX_EXTRA_CLIENT_REDIRECT_URIS` parsing.
- [x] T13 Unit: `build_mcp_auth` wiring — CIMD on, loopback + extra patterns in the
      allowlist, CIMD manager sharing that same allowlist.
- [x] T14 README / AGENTS.md / `.env.example` updates.

### Implementation Notes

Verified against a live metadata dump before and after: `client_id_metadata_document_supported`
appears only post-upgrade, and `token_endpoint_auth_methods_supported` gains
`private_key_jwt` + `none`. Full suite: 611 passing.

Not verifiable from the dev box: a real end-to-end CIMD authorize needs a hosted client
document and Clerk credentials. First hosted client added will also need its callback
in `PKTX_EXTRA_CLIENT_REDIRECT_URIS`.
