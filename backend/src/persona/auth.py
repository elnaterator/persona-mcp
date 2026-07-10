"""Clerk JWT validation and FastAPI dependency for authenticated user context."""

import logging
import os
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.oauth_proxy import OAuthProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth.redirect_validation import DEFAULT_LOCALHOST_PATTERNS
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from persona.database import upsert_user
from persona.db import DBConnection

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

logger = logging.getLogger("persona")

# ContextVar for passing user identity into MCP tool handlers
# Set to the Clerk user_id string when a request is authenticated;
# None when running in stdio mode without a user context.
current_user_id_var: ContextVar[str | None] = ContextVar(
    "current_user_id", default=None
)


def require_user_id() -> str:
    """Return the current user ID from the context var, or raise.

    MCP tool handlers MUST call this to enforce user scoping.
    Raises RuntimeError when no authenticated user context is set.
    """
    user_id = current_user_id_var.get()
    if user_id is None:
        raise RuntimeError("No user context set — cannot access user data")
    return user_id


# ---------------------------------------------------------------------------
# JWKS in-memory cache (used by REST API JWT path)
# ---------------------------------------------------------------------------

_JWKS_CACHE: dict[str, Any] = {}  # kid -> key dict
_JWKS_FETCHED_AT: float = 0.0
_JWKS_TTL: float = 3600.0  # 1 hour


def _jwks_url() -> str:
    return os.environ.get("CLERK_JWKS_URL", "")


def _issuer() -> str:
    return os.environ.get("CLERK_ISSUER", "")


def _fetch_jwks() -> dict[str, Any]:
    """Fetch JWKS from Clerk and update the in-memory cache."""
    global _JWKS_CACHE, _JWKS_FETCHED_AT
    url = _jwks_url()
    if not url:
        raise ValueError("CLERK_JWKS_URL is not configured")
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    data = response.json()
    keys: dict[str, Any] = {}
    for key in data.get("keys", []):
        kid = key.get("kid")
        if kid:
            keys[kid] = key
    _JWKS_CACHE = keys
    _JWKS_FETCHED_AT = time.monotonic()
    logger.debug("JWKS refreshed, %d keys cached", len(keys))
    return keys


def _get_jwks_key(kid: str) -> dict[str, Any]:
    """Return the JWK for the given kid, refreshing cache if needed."""
    global _JWKS_CACHE, _JWKS_FETCHED_AT

    now = time.monotonic()
    cache_age = now - _JWKS_FETCHED_AT

    # Serve from cache if fresh and kid is present
    if cache_age < _JWKS_TTL and kid in _JWKS_CACHE:
        return _JWKS_CACHE[kid]

    # Refresh cache (either expired TTL or unknown kid)
    keys = _fetch_jwks()
    if kid not in keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown signing key",
        )
    return keys[kid]


# ---------------------------------------------------------------------------
# JWT verification (REST API path)
# ---------------------------------------------------------------------------


def verify_clerk_jwt(token: str) -> dict[str, Any]:
    """Validate a Clerk JWT and return its claims.

    Raises:
        HTTPException 401: If the token is missing, expired, wrong issuer, or invalid.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token header: {exc}",
        ) from exc

    kid = unverified_header.get("kid", "")
    key = _get_jwks_key(kid)

    issuer = _issuer()
    if not issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CLERK_ISSUER is not configured",
        )

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_aud": False},
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {exc}",
        ) from exc

    if not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    return claims


# ---------------------------------------------------------------------------
# UserContext and FastAPI dependency (REST API)
# ---------------------------------------------------------------------------


@dataclass
class UserContext:
    """Authenticated user identity extracted from a valid Clerk JWT."""

    id: str
    email: str | None
    display_name: str | None


_bearer = HTTPBearer(auto_error=False)


def build_get_current_user(conn: DBConnection):  # type: ignore[no-untyped-def]
    """Return a FastAPI dependency that validates JWTs and upserts users."""

    def _dep(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> UserContext:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
            )
        claims = verify_clerk_jwt(credentials.credentials)

        user_id: str = claims["sub"]
        email: str | None = claims.get("email") or claims.get("primary_email_address")
        display_name: str | None = (
            claims.get("name") or claims.get("display_name") or claims.get("username")
        )

        upsert_user(conn, user_id, email, display_name)
        return UserContext(id=user_id, email=email, display_name=display_name)

    return _dep


# ---------------------------------------------------------------------------
# MCP OAuth2 resource server auth (FastMCP RemoteAuthProvider + JWTVerifier)
# ---------------------------------------------------------------------------


class _DiagnosticJWTVerifier(JWTVerifier):
    """JWTVerifier that records why a token was rejected, for diagnosis.

    FastMCP's JWTVerifier swallows validation failures, returns ``None``, and
    logs the reason only on its own logger — so our logs show a bare 401
    invalid_token with no cause. This subclass re-logs the rejection on the
    ``persona`` logger at DEBUG, including the token's unverified header/claims
    next to the expected issuer, making a mismatch (alg, kid, issuer, or an
    opaque non-JWT token) diagnosable. Verification behaviour is unchanged.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        result = await super().verify_token(token)
        if result is None and logger.isEnabledFor(logging.DEBUG):
            self._log_rejection(token)
        return result

    def _log_rejection(self, token: str) -> None:
        try:
            header = jwt.get_unverified_header(token)
        except JWTError as exc:
            logger.debug("MCP token rejected: not a parseable JWT (%s)", exc)
            return
        try:
            claims = jwt.get_unverified_claims(token)
        except JWTError:
            claims = {}
        logger.debug(
            "MCP token rejected: alg=%s kid=%s token_iss=%s token_aud=%s exp=%s "
            "(expected_iss=%s jwks=%s)",
            header.get("alg"),
            header.get("kid"),
            claims.get("iss"),
            claims.get("aud"),
            claims.get("exp"),
            self.issuer,
            self.jwks_uri,
        )


def build_mcp_auth(pool: "ConnectionPool[Any]") -> OAuthProxy:
    """Build the FastMCP OAuth proxy for the /mcp endpoint.

    Requires PERSONA_PUBLIC_URL, CLERK_JWKS_URL, CLERK_ISSUER,
    CLERK_OAUTH_CLIENT_ID, CLERK_OAUTH_CLIENT_SECRET env vars.

    The proxy handles Dynamic Client Registration locally so native MCP clients
    (Claude Desktop, Cursor, VS Code) register with *us*, not Clerk — fixing the
    loopback redirect mismatch where a client registers http://localhost:PORT but
    sends http://127.0.0.1:PORT (distinct strings per OAuth, both allowed here by
    FastMCP's default localhost patterns). Authorize/token are proxied upstream to
    Clerk via one fixed pre-registered redirect URI; the proxy issues its own
    reference JWTs to clients and validates the stored Clerk token on every call.

    Proxy state (registrations, encrypted upstream tokens, JTI mappings, transient
    authorize state) is stored in PostgreSQL via ``pool`` so it is shared across
    serverless instances rather than a per-instance local DiskStore.

    Token audience is NOT validated: signature (JWKS) and issuer stay strict.
    """
    from persona.config import (
        resolve_clerk_issuer,
        resolve_clerk_jwks_url,
        resolve_clerk_oauth_client_id,
        resolve_clerk_oauth_client_secret,
        resolve_public_url,
    )
    from persona.oauth_store import build_oauth_client_storage

    public = resolve_public_url()
    issuer = resolve_clerk_issuer()
    jwks_uri = resolve_clerk_jwks_url()
    client_secret = resolve_clerk_oauth_client_secret()
    verifier = _DiagnosticJWTVerifier(
        jwks_uri=jwks_uri,
        issuer=issuer,
        audience=None,
        base_url=public,
    )
    logger.info(
        "MCP OAuth proxy configured: issuer=%s jwks_uri=%s resource=%s/mcp",
        issuer,
        jwks_uri,
        public,
    )
    return OAuthProxy(
        upstream_authorization_endpoint=f"{issuer}/oauth/authorize",
        upstream_token_endpoint=f"{issuer}/oauth/token",
        upstream_client_id=resolve_clerk_oauth_client_id(),
        upstream_client_secret=client_secret,
        token_verifier=verifier,
        base_url=public,
        redirect_path="/auth/callback",
        # Loopback tolerance: a client that registers http://127.0.0.1:PORT may
        # authorize with http://localhost:PORT (or vice versa) — distinct strings
        # per OAuth. These patterns accept either host on any port so the mismatch
        # no longer 400s, while still rejecting non-loopback redirects a client
        # never registered. Extend this list if a hosted (non-loopback) client is
        # ever added.
        allowed_client_redirect_uris=list(DEFAULT_LOCALHOST_PATTERNS),
        # Shared, encrypted proxy state in PostgreSQL (not a local DiskStore) so
        # the OAuth flow survives across serverless instances and cold starts. The
        # Fernet key is derived from the Clerk OAuth client secret, stable per env.
        client_storage=build_oauth_client_storage(pool, client_secret),
    )


# ---------------------------------------------------------------------------
# MCP tool middleware: bridge access token sub → current_user_id_var
# ---------------------------------------------------------------------------

# Module-level reference to DB connection, set by server.py at startup.
_conn: DBConnection | None = None


class UserContextToolMiddleware(Middleware):
    """Set current_user_id_var from the FastMCP access token for each tool call."""

    async def on_call_tool(self, context, call_next):  # type: ignore[override]
        tok = get_access_token()
        sub = (tok.claims or {}).get("sub") if tok else None
        reset = current_user_id_var.set(sub)
        try:
            if sub and _conn is not None:
                try:
                    upsert_user(_conn, sub, None, None)
                except Exception as exc:
                    logger.warning("upsert_user failed in MCP tool middleware: %s", exc)
            return await call_next(context)
        finally:
            current_user_id_var.reset(reset)
