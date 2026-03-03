"""Persona server — FastAPI REST API + MCP tools, with --stdio backward compat."""

import argparse
import logging
import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Any, cast

import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastmcp import FastMCP
from psycopg_pool import ConnectionPool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse

from persona.accomplishment_service import AccomplishmentService
from persona.api.routes import create_router
from persona.application_service import ApplicationService
from persona.auth import build_get_current_user
from persona.config import (
    configure_logging,
    resolve_clerk_secret_key,
    resolve_cors_origins,
    resolve_db_url,
    resolve_frontend_dir,
    resolve_pool_max,
    resolve_pool_min,
    resolve_port,
)
from persona.database import init_pool, upsert_user
from persona.db import DBConnection
from persona.resume_service import ResumeService
from persona.tools.accomplishment_tools import register_accomplishment_tools
from persona.tools.application_tools import register_application_tools
from persona.tools.resume_tools import register_resume_tools

logger = logging.getLogger("persona")

mcp = FastMCP("persona")

# Resolved at startup, used by MCP tool handlers.
_pool: ConnectionPool[Any] | None = None
_raw_conn: Any = None  # raw psycopg.Connection — needed for pool.putconn()
_conn: DBConnection | None = None
_service: ResumeService | None = None
_app_service: ApplicationService | None = None
_acc_service: AccomplishmentService | None = None


def _get_resume_service() -> ResumeService:
    assert _service is not None
    return _service


def _get_app_service() -> ApplicationService:
    assert _app_service is not None
    return _app_service


def _get_acc_service() -> AccomplishmentService:
    assert _acc_service is not None
    return _acc_service


def get_db() -> Generator[DBConnection, None, None]:
    """FastAPI dependency: yields a per-request PostgreSQL connection from the pool."""
    assert _pool is not None, "Database pool not initialized"
    with _pool.connection() as conn:
        yield cast(DBConnection, conn)


# Register MCP tools from modules
register_resume_tools(mcp, _get_resume_service)
register_application_tools(mcp, _get_app_service)
register_accomplishment_tools(mcp, _get_acc_service)


# --- UserContextMiddleware ---


class UserContextMiddleware(BaseHTTPMiddleware):
    """Set current_user_id_var from Bearer token or PERSONA_USER_ID env var.

    For /mcp paths: enforces dual-auth (JWT + API key) via the Clerk SDK.
      - Missing or invalid token → 401 Unauthorized.
      - Valid token → sets current_user_id_var and calls next handler.

    For all other paths: attempts JWT-only auth (backward compat for REST API
    callers that also set the context var) but never blocks the request.
    """

    async def dispatch(self, request: StarletteRequest, call_next):  # type: ignore[override]
        from persona.auth import (
            authenticate_mcp_request,
            build_clerk_client,
            current_user_id_var,
            extract_user_id_from_request_state,
            verify_clerk_jwt,
        )

        # -------------------------------------------------------------------
        # /mcp paths: enforce dual-auth (Clerk SDK — JWT + API key)
        # -------------------------------------------------------------------
        if request.url.path.startswith("/mcp"):
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"},
                )

            try:
                secret_key = resolve_clerk_secret_key()
                clerk_client = build_clerk_client(secret_key)
                request_state = authenticate_mcp_request(request, clerk_client)
            except RuntimeError as exc:
                logger.error("Clerk configuration error: %s", exc)
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Authentication service not configured"},
                )
            except Exception as exc:
                logger.exception("Clerk authentication error: %s", exc)
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication failed"},
                )

            if not request_state.is_signed_in:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": request_state.message or "Not authenticated"},
                )

            user_id = extract_user_id_from_request_state(request_state)
            if user_id and _conn is not None:
                try:
                    upsert_user(_conn, user_id, email=None, display_name=None)
                except Exception as exc:
                    logger.warning("upsert_user failed in MCP auth: %s", exc)

            token_ctx = current_user_id_var.set(user_id)
            try:
                return await call_next(request)
            finally:
                current_user_id_var.reset(token_ctx)

        # -------------------------------------------------------------------
        # Non-/mcp paths: try JWT auth (sets context var), never blocks
        # -------------------------------------------------------------------
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                claims = verify_clerk_jwt(token)
                token_ctx = current_user_id_var.set(claims.get("sub"))
                try:
                    return await call_next(request)
                finally:
                    current_user_id_var.reset(token_ctx)
            except Exception:
                pass

        # Also support stdio mode: check env var
        stdio_user = os.environ.get("PERSONA_USER_ID")
        if stdio_user:
            token_ctx = current_user_id_var.set(stdio_user)
            try:
                return await call_next(request)
            finally:
                current_user_id_var.reset(token_ctx)

        return await call_next(request)


# --- FastAPI application factory ---


def create_app(
    service: ResumeService | None = None,
    conn: DBConnection | None = None,
) -> FastAPI:
    """Create the FastAPI application with REST API routes and CORS middleware.

    Args:
        service: Optional pre-built ResumeService (for testing).
        conn: Optional pre-built DBConnection (for testing / MCP globals).
            If service and conn are None, initializes pool from environment config.
    """
    global _pool, _raw_conn, _conn, _service, _app_service, _acc_service

    # Track production mode before service is overwritten below.
    # Auth is only wired in production (no pre-built service injected).
    _production_mode = service is None

    if service is None:
        logger = configure_logging()
        resolve_clerk_secret_key()  # Startup validation — fail fast if key is missing
        _pool = init_pool(resolve_db_url(), resolve_pool_min(), resolve_pool_max())
        raw = _pool.getconn()
        raw.autocommit = True
        _raw_conn = raw
        conn = cast(DBConnection, raw)
        service = ResumeService(conn)
        logger.info("Persona server starting (PostgreSQL pool initialized)")

    _conn = conn
    _service = service
    _app_service = ApplicationService(conn) if conn else None
    _acc_service = AccomplishmentService(conn) if conn else None

    # Get MCP HTTP app — use path="/mcp" so the Route is registered at /mcp.
    # We add this route directly to FastAPI's router (not via app.mount)
    # because Starlette's Mount("/mcp") regex requires a trailing slash,
    # causing POST /mcp to fall through to StaticFiles → 405.
    mcp_app = mcp.http_app(path="/mcp")

    # Create combined lifespan that wraps MCP lifespan and closes pool on shutdown
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Startup: delegate to MCP lifespan
        async with mcp_app.lifespan(app):
            yield
        # Shutdown: return connection to pool, then close pool
        if _pool is not None:
            if _raw_conn is not None:
                _pool.putconn(_raw_conn)
            _pool.close()

    app = FastAPI(title="Persona", lifespan=lifespan)

    # CORS middleware
    cors_origins = resolve_cors_origins()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # UserContextMiddleware: populate current_user_id_var for MCP tool handlers
    app.add_middleware(UserContextMiddleware)

    # Wire auth in production mode only; test callers that inject a pre-built
    # service bypass auth so existing cross-interface tests keep working.
    get_user = (
        build_get_current_user(conn) if _production_mode and conn is not None else None
    )
    app.include_router(
        create_router(
            service,
            app_service=_app_service,
            acc_service=_acc_service,
            get_current_user=get_user,
        )
    )

    # Add MCP routes directly to FastAPI's router (not via app.mount) so
    # the /mcp route is matched before the StaticFiles catch-all.
    for route in mcp_app.routes:
        app.router.routes.append(route)

    # Mount static files for frontend (if directory exists)
    # This must come AFTER API routes and MCP mount so they take priority
    frontend_dir = resolve_frontend_dir()
    if frontend_dir is not None:
        app.mount(
            "/",
            StaticFiles(directory=str(frontend_dir), html=True),
            name="frontend",
        )

    return app


def main() -> None:
    """Start the persona server (HTTP default, --stdio for backward compat)."""
    parser = argparse.ArgumentParser(description="Persona server")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run in stdio MCP mode (backward compat for local MCP clients)",
    )
    args = parser.parse_args()

    if args.stdio:
        global _pool, _raw_conn, _conn, _service, _app_service, _acc_service
        logger = configure_logging()
        _pool = init_pool(resolve_db_url(), resolve_pool_min(), resolve_pool_max())
        raw = _pool.getconn()
        raw.autocommit = True
        _raw_conn = raw
        _conn = cast(DBConnection, raw)
        _service = ResumeService(_conn)
        _app_service = ApplicationService(_conn)
        _acc_service = AccomplishmentService(_conn)
        logger.info("Persona MCP server starting (stdio, PostgreSQL pool initialized)")
        try:
            mcp.run(transport="stdio")
        finally:
            _pool.putconn(_raw_conn)
            _pool.close()
    else:
        port = resolve_port()
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
