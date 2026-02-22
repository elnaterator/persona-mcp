"""Persona server — FastAPI REST API + MCP tools, with --stdio backward compat."""

import argparse
import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Any, cast

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastmcp import FastMCP
from psycopg_pool import ConnectionPool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from persona.accomplishment_service import AccomplishmentService
from persona.api.routes import create_router
from persona.application_service import ApplicationService
from persona.auth import build_get_current_user
from persona.config import (
    configure_logging,
    resolve_cors_origins,
    resolve_db_url,
    resolve_frontend_dir,
    resolve_pool_max,
    resolve_pool_min,
    resolve_port,
)
from persona.database import init_pool
from persona.db import DBConnection
from persona.resume_service import ResumeService
from persona.tools.accomplishment_tools import register_accomplishment_tools
from persona.tools.application_tools import register_application_tools
from persona.tools.resume_tools import register_resume_tools

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
    """Set current_user_id_var from Bearer JWT or PERSONA_USER_ID env var."""

    async def dispatch(self, request: StarletteRequest, call_next):  # type: ignore[override]
        from persona.auth import current_user_id_var, verify_clerk_jwt

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

    # Get MCP HTTP app first to access its lifespan
    mcp_app = mcp.http_app(path="/")

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

    # Mount MCP server at /mcp (streamable-http transport)
    app.mount("/mcp", mcp_app)

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
