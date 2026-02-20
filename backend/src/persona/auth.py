"""Clerk JWT validation and FastAPI dependency for authenticated user context."""

import logging
import os
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from persona.database import upsert_user
from persona.db import DBConnection

logger = logging.getLogger("persona")

# ContextVar for passing user identity into MCP tool handlers
# Set to the Clerk user_id string when a request is authenticated;
# None when running in stdio mode without a user context.
current_user_id_var: ContextVar[str | None] = ContextVar(
    "current_user_id", default=None
)

# ---------------------------------------------------------------------------
# JWKS in-memory cache
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
# JWT verification
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
# UserContext and FastAPI dependency
# ---------------------------------------------------------------------------


@dataclass
class UserContext:
    """Authenticated user identity extracted from a valid Clerk JWT."""

    id: str
    email: str | None
    display_name: str | None


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: DBConnection | None = None,
) -> UserContext:
    """FastAPI dependency: validate Bearer JWT, upsert user row, return UserContext.

    This function is called as a dependency factory; the actual FastAPI
    dependency is built via ``build_get_current_user(conn)`` below.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    claims = verify_clerk_jwt(credentials.credentials)

    user_id: str = claims["sub"]
    # Clerk puts primary email in email_addresses or the "email" custom claim
    email: str | None = claims.get("email") or claims.get("primary_email_address")
    display_name: str | None = (
        claims.get("name") or claims.get("display_name") or claims.get("username")
    )

    if conn is not None:
        upsert_user(conn, user_id, email, display_name)

    return UserContext(id=user_id, email=email, display_name=display_name)


def build_get_current_user(conn: DBConnection):  # type: ignore[no-untyped-def]
    """Return a FastAPI dependency that validates JWTs and upserts users.

    Usage::

        router.add_api_route(
            "/api/foo", handler,
            dependencies=[Depends(build_get_current_user(conn))]
        )

        # Or as a parameter:
        def handler(current_user: UserContext = Depends(build_get_current_user(conn))):
            ...
    """

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
