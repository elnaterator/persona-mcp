"""Persona server — FastAPI REST API + MCP tools, with --stdio backward compat."""

import argparse
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP

from backend.api.routes import create_router
from backend.config import (
    configure_logging,
    resolve_cors_origins,
    resolve_data_dir,
    resolve_port,
)
from backend.database import init_database
from backend.db import DBConnection
from backend.resume_service import ResumeService

mcp = FastMCP("persona")

# Resolved at startup, used by MCP tool handlers.
_conn: DBConnection | None = None
_service: ResumeService | None = None


# --- MCP tool definitions (unchanged signatures) ---


@mcp.tool()
def get_resume() -> dict[str, Any]:
    """Get the full resume as structured data.

    Returns contact info, summary, experience, education, and skills.
    """
    assert _service is not None
    return _service.get_resume().model_dump()


@mcp.tool()
def get_resume_section(section: str) -> Any:
    """Get a specific resume section by name.

    Args:
        section: One of: contact, summary, experience, education, skills.
    """
    assert _service is not None
    return _service.get_section(section)


@mcp.tool()
def update_section(section: str, data: dict[str, Any]) -> str:
    """Update a non-list resume section (contact info or summary).

    Args:
        section: One of: contact, summary.
        data: Fields to update. For contact: any subset of contact fields.
              For summary: {"text": "new summary"}.
    """
    assert _service is not None
    return _service.update_section(section, data)


@mcp.tool()
def add_entry(section: str, data: dict[str, Any]) -> str:
    """Add an entry to a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        data: Entry fields. Required fields vary by section.
    """
    assert _service is not None
    return _service.add_entry(section, data)


@mcp.tool()
def update_entry(section: str, index: int, data: dict[str, Any]) -> str:
    """Update an existing entry in a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        index: 0-based index of the entry to update.
        data: Fields to update (partial update, omitted fields unchanged).
    """
    assert _service is not None
    return _service.update_entry(section, index, data)


@mcp.tool()
def remove_entry(section: str, index: int) -> str:
    """Remove an entry from a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        index: 0-based index of the entry to remove.
    """
    assert _service is not None
    return _service.remove_entry(section, index)


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
    global _conn, _service

    if service is None:
        logger = configure_logging()
        data_dir = resolve_data_dir()
        conn = init_database(data_dir)
        service = ResumeService(conn)
        logger.info("Persona server starting, data dir: %s", data_dir)

    _conn = conn
    _service = service

    # Get MCP HTTP app first to access its lifespan
    mcp_app = mcp.http_app(path="/")

    # Use MCP app's lifespan directly as required by FastMCP
    # We close the DB connection when the app shuts down via a shutdown event handler
    app = FastAPI(title="Persona", lifespan=mcp_app.lifespan)

    # Register shutdown event to close DB connection
    @app.on_event("shutdown")
    def shutdown_event() -> None:
        if _conn is not None:
            _conn.close()

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
    app.include_router(create_router(service))

    # Mount MCP server at /mcp (streamable-http transport)
    app.mount("/mcp", mcp_app)

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
        global _conn, _service
        logger = configure_logging()
        data_dir = resolve_data_dir()
        _conn = init_database(data_dir)
        _service = ResumeService(_conn)
        logger.info("Persona MCP server starting (stdio), data dir: %s", data_dir)
        mcp.run(transport="stdio")
    else:
        port = resolve_port()
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=port)
