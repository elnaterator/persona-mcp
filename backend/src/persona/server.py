"""Persona server — FastAPI REST API + MCP tools, with --stdio backward compat."""

import argparse
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastmcp import FastMCP

from persona.api.routes import create_router
from persona.application_service import ApplicationService
from persona.config import (
    configure_logging,
    resolve_cors_origins,
    resolve_data_dir,
    resolve_frontend_dir,
    resolve_port,
)
from persona.database import init_database
from persona.db import DBConnection
from persona.resume_service import ResumeService
from persona.tools.application_tools import register_application_tools
from persona.tools.resume_tools import register_resume_tools

mcp = FastMCP("persona")

# Resolved at startup, used by MCP tool handlers.
_conn: DBConnection | None = None
_service: ResumeService | None = None
_app_service: ApplicationService | None = None


def _get_resume_service() -> ResumeService:
    assert _service is not None
    return _service


def _get_app_service() -> ApplicationService:
    assert _app_service is not None
    return _app_service


# Register MCP tools from modules
register_resume_tools(mcp, _get_resume_service)
register_application_tools(mcp, _get_app_service)


# --- FastAPI application factory ---


def create_app(
    service: ResumeService | None = None,
    conn: DBConnection | None = None,
) -> FastAPI:
    """Create the FastAPI application with REST API routes and CORS middleware.

    Args:
        service: Optional pre-built ResumeService (for testing).
        conn: Optional pre-built DBConnection (for testing / MCP globals).
            If service and conn are None, initializes from environment config.
    """
    global _conn, _service, _app_service

    if service is None:
        logger = configure_logging()
        data_dir = resolve_data_dir()
        conn = init_database(data_dir)
        service = ResumeService(conn)
        logger.info("Persona server starting, data dir: %s", data_dir)

    _conn = conn
    _service = service
    _app_service = ApplicationService(conn) if conn else None

    # Get MCP HTTP app first to access its lifespan
    mcp_app = mcp.http_app(path="/")

    # Create combined lifespan that wraps MCP lifespan and closes DB on shutdown
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Startup: delegate to MCP lifespan
        async with mcp_app.lifespan(app):
            yield
        # Shutdown: close DB connection
        if _conn is not None:
            _conn.close()

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

    # Mount REST API routes
    app.include_router(
        create_router(
            service,
            app_service=_app_service,
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
        global _conn, _service, _app_service
        logger = configure_logging()
        data_dir = resolve_data_dir()
        _conn = init_database(data_dir)
        _service = ResumeService(_conn)
        _app_service = ApplicationService(_conn)
        logger.info("Persona MCP server starting (stdio), data dir: %s", data_dir)
        mcp.run(transport="stdio")
    else:
        port = resolve_port()
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
