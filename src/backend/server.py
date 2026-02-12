"""Persona server — FastAPI REST API + MCP tools, with --stdio backward compat."""

import argparse
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

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
from backend.tools import read as read_tools
from backend.tools import write as write_tools

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
    assert _conn is not None
    return read_tools.get_resume(conn=_conn)


@mcp.tool()
def get_resume_section(section: str) -> Any:
    """Get a specific resume section by name.

    Args:
        section: One of: contact, summary, experience, education, skills.
    """
    assert _conn is not None
    return read_tools.get_resume_section(section=section, conn=_conn)


@mcp.tool()
def update_section(section: str, data: dict[str, Any]) -> str:
    """Update a non-list resume section (contact info or summary).

    Args:
        section: One of: contact, summary.
        data: Fields to update. For contact: any subset of contact fields.
              For summary: {"text": "new summary"}.
    """
    assert _conn is not None
    return write_tools.update_section(section=section, data=data, conn=_conn)


@mcp.tool()
def add_entry(section: str, data: dict[str, Any]) -> str:
    """Add an entry to a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        data: Entry fields. Required fields vary by section.
    """
    assert _conn is not None
    return write_tools.add_entry(section=section, data=data, conn=_conn)


@mcp.tool()
def update_entry(section: str, index: int, data: dict[str, Any]) -> str:
    """Update an existing entry in a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        index: 0-based index of the entry to update.
        data: Fields to update (partial update, omitted fields unchanged).
    """
    assert _conn is not None
    return write_tools.update_entry(section=section, index=index, data=data, conn=_conn)


@mcp.tool()
def remove_entry(section: str, index: int) -> str:
    """Remove an entry from a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        index: 0-based index of the entry to remove.
    """
    assert _conn is not None
    return write_tools.remove_entry(section=section, index=index, conn=_conn)


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

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
        yield
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

    app.include_router(create_router(service))

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
        global _conn
        logger = configure_logging()
        data_dir = resolve_data_dir()
        _conn = init_database(data_dir)
        logger.info("Persona MCP server starting (stdio), data dir: %s", data_dir)
        mcp.run(transport="stdio")
    else:
        port = resolve_port()
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=port)
