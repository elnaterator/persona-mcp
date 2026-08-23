"""pktx server — FastAPI REST API + MCP tools, with --stdio backward compat."""

import argparse
import logging
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
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.routing import Route as StarletteRoute

from pktx.accomplishment_service import AccomplishmentService
from pktx.api.routes import create_router
from pktx.application_service import ApplicationService
from pktx.auth import (
    UserContextToolMiddleware,
    build_get_current_user,
    build_mcp_auth,
    current_user_id_var,
    verify_clerk_jwt,
)
from pktx.communication_service import ContactCommunicationService
from pktx.config import (
    configure_logging,
    resolve_cors_origins,
    resolve_db_url,
    resolve_frontend_dir,
    resolve_pool_max,
    resolve_pool_min,
    resolve_port,
)
from pktx.contact_service import ContactService
from pktx.database import init_pool
from pktx.db import DBConnection
from pktx.link_service import LinkService
from pktx.note_service import NoteService
from pktx.resume_service import ResumeService
from pktx.tools.accomplishment_tools import register_accomplishment_tools
from pktx.tools.application_tools import register_application_tools
from pktx.tools.contact_tools import register_contact_tools
from pktx.tools.link_tools import register_link_tools
from pktx.tools.note_tools import register_note_tools
from pktx.tools.resume_tools import register_resume_tools

logger = logging.getLogger("pktx")


class SPAStaticFiles(StaticFiles):
    """StaticFiles subclass that falls back to index.html for unknown paths.

    Enables client-side routing (React Router) to handle routes like
    /resumes/3 when accessed directly or on page refresh, instead of
    returning a 404 from the server.

    API routes and MCP routes are registered before this mount and take
    priority, so /api/*, /health, and /mcp/* are never intercepted.
    """

    async def get_response(self, path: str, scope):  # type: ignore[override]
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


# Resolved at startup, used by MCP tool handlers.
_pool: ConnectionPool[Any] | None = None
_raw_conn: Any = None  # raw psycopg.Connection — needed for pool.putconn()
_conn: DBConnection | None = None
_service: ResumeService | None = None
_app_service: ApplicationService | None = None
_acc_service: AccomplishmentService | None = None
_note_service: NoteService | None = None
_contact_service: ContactService | None = None
_comm_service: ContactCommunicationService | None = None
_link_service: LinkService | None = None


def _get_resume_service() -> ResumeService:
    assert _service is not None
    return _service


def _get_app_service() -> ApplicationService:
    assert _app_service is not None
    return _app_service


def _get_acc_service() -> AccomplishmentService:
    assert _acc_service is not None
    return _acc_service


def _get_note_service() -> NoteService:
    assert _note_service is not None
    return _note_service


def _get_contact_service() -> ContactService:
    assert _contact_service is not None
    return _contact_service


def _get_comm_service() -> ContactCommunicationService:
    assert _comm_service is not None
    return _comm_service


def _get_link_service() -> LinkService:
    assert _link_service is not None
    return _link_service


def get_db() -> Generator[DBConnection, None, None]:
    """FastAPI dependency: yields a per-request PostgreSQL connection from the pool."""
    assert _pool is not None, "Database pool not initialized"
    with _pool.connection() as conn:
        yield cast(DBConnection, conn)


def _build_mcp(production: bool) -> FastMCP:
    """Create FastMCP instance, register all tools, and wire auth/middleware."""
    import pktx.auth as auth_module

    if production:
        assert _pool is not None, "DB pool required for production MCP auth"
        mcp_auth = build_mcp_auth(_pool)
    else:
        mcp_auth = None
    m = FastMCP("pktx", auth=mcp_auth)

    register_resume_tools(m, _get_resume_service)
    register_application_tools(m, _get_app_service)
    register_accomplishment_tools(m, _get_acc_service)
    register_note_tools(m, _get_note_service)
    register_contact_tools(m, _get_contact_service, _get_comm_service)
    register_link_tools(m, _get_link_service)

    if production:
        m.add_middleware(UserContextToolMiddleware())
        # Expose the shared conn reference to the tool middleware
        auth_module._conn = _conn

    return m


# --- UserContextMiddleware ---


class UserContextMiddleware(BaseHTTPMiddleware):
    """Set current_user_id_var from Bearer token or PKTX_USER_ID env var.

    REST API paths: attempts JWT-only auth (sets context var), never blocks.
    stdio mode: reads PKTX_USER_ID env var.
    MCP paths are handled by UserContextToolMiddleware via FastMCP middleware.
    """

    async def dispatch(self, request: StarletteRequest, call_next):  # type: ignore[override]
        # Non-/mcp paths: try JWT auth (sets context var), never blocks
        if not request.url.path.startswith("/mcp"):
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
        stdio_user = os.environ.get("PKTX_USER_ID")
        if stdio_user:
            token_ctx = current_user_id_var.set(stdio_user)
            try:
                return await call_next(request)
            finally:
                current_user_id_var.reset(token_ctx)

        return await call_next(request)


_PRM_PATH = "/.well-known/oauth-protected-resource"


def _add_root_resource_metadata_alias(app: FastAPI, mcp_app: Any) -> None:
    """Serve protected-resource metadata at the root well-known path too.

    FastMCP registers RFC 9728 metadata only at the path-suffixed location
    (``/.well-known/oauth-protected-resource/mcp``). MCP clients probe that first
    and fall back to the root path, so a client that skips the WWW-Authenticate
    header and probes only the root would otherwise get the SPA's 404 page. Both
    paths serve the same document, produced by the same handler.
    """
    suffixed = f"{_PRM_PATH}/mcp"
    source = next(
        (r for r in mcp_app.routes if getattr(r, "path", None) == suffixed), None
    )
    if source is None:
        return
    app.router.routes.append(
        StarletteRoute(
            _PRM_PATH,
            endpoint=source.endpoint,
            methods=["GET", "HEAD", "OPTIONS"],
            name="oauth_protected_resource_root",
        )
    )


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
    global _pool, _raw_conn, _conn, _service
    global _app_service, _acc_service, _note_service, _contact_service, _comm_service
    global _link_service

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
        logger.info("pktx server starting (PostgreSQL pool initialized)")

    _conn = conn
    _service = service
    _app_service = ApplicationService(conn) if conn else None
    _acc_service = AccomplishmentService(conn) if conn else None
    _note_service = NoteService(conn) if conn else None
    _contact_service = ContactService(conn) if conn else None
    _comm_service = ContactCommunicationService(conn) if conn else None
    _link_service = LinkService(conn) if conn else None

    mcp = _build_mcp(production=_production_mode)

    # Get MCP HTTP app — use path="/mcp" so the Route is registered at /mcp.
    # We add this route directly to FastAPI's router (not via app.mount)
    # because Starlette's Mount("/mcp") regex requires a trailing slash,
    # causing POST /mcp to fall through to StaticFiles → 405.
    mcp_app = mcp.http_app(path="/mcp", stateless_http=True)

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

    app = FastAPI(title="pktx", lifespan=lifespan)

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

    # UserContextMiddleware: populate current_user_id_var for REST API handlers
    app.add_middleware(UserContextMiddleware)

    # Re-apply the MCP auth middleware that mcp.http_app() installs at the app
    # level. Below we graft only `mcp_app.routes` into this FastAPI app (to keep
    # POST /mcp working without a trailing slash); that drops the app-level
    # AuthenticationMiddleware (runs BearerAuthBackend → verify_token) and
    # AuthContextMiddleware (powers get_access_token() for tool user-scoping).
    # Without them every /mcp request is treated as unauthenticated and the
    # per-route RequireAuthMiddleware 401s as invalid_token before our verifier
    # ever runs. Add in reverse so AuthenticationMiddleware stays outermost and
    # populates request auth before AuthContextMiddleware reads it.
    if _production_mode and mcp.auth is not None:
        for mw in reversed(mcp.auth.get_middleware()):
            app.add_middleware(mw.cls, *mw.args, **mw.kwargs)

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
            note_service=_note_service,
            contact_service=_contact_service,
            comm_service=_comm_service,
            link_service=_link_service,
            get_current_user=get_user,
        )
    )

    # Add MCP routes directly to FastAPI's router (not via app.mount) so
    # the /mcp route is matched before the StaticFiles catch-all.
    for route in mcp_app.routes:
        app.router.routes.append(route)

    _add_root_resource_metadata_alias(app, mcp_app)

    # Mount static files for frontend (if directory exists)
    # This must come AFTER API routes and MCP mount so they take priority
    frontend_dir = resolve_frontend_dir()
    if frontend_dir is not None:
        app.mount(
            "/",
            SPAStaticFiles(directory=str(frontend_dir), html=True),
            name="frontend",
        )

    return app


def main() -> None:
    """Start the pktx server (HTTP default, --stdio for backward compat)."""
    parser = argparse.ArgumentParser(description="pktx server")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run in stdio MCP mode (backward compat for local MCP clients)",
    )
    args = parser.parse_args()

    if args.stdio:
        global _pool, _raw_conn, _conn, _service
        global _app_service, _acc_service, _note_service, _contact_service
        global _comm_service, _link_service
        logger = configure_logging()
        _pool = init_pool(resolve_db_url(), resolve_pool_min(), resolve_pool_max())
        raw = _pool.getconn()
        raw.autocommit = True
        _raw_conn = raw
        _conn = cast(DBConnection, raw)
        _service = ResumeService(_conn)
        _app_service = ApplicationService(_conn)
        _acc_service = AccomplishmentService(_conn)
        _note_service = NoteService(_conn)
        _contact_service = ContactService(_conn)
        _comm_service = ContactCommunicationService(_conn)
        _link_service = LinkService(_conn)
        logger.info("pktx MCP server starting (stdio, PostgreSQL pool initialized)")
        mcp = _build_mcp(production=False)
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
