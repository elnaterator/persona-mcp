"""Persona MCP server — entry point and FastMCP setup."""

import sqlite3
from typing import Any

from mcp.server.fastmcp import FastMCP

from persona.config import configure_logging, resolve_data_dir
from persona.database import init_database
from persona.tools import read as read_tools
from persona.tools import write as write_tools

mcp = FastMCP("persona")

# Resolved at startup in main(), used by tool handlers.
_conn: sqlite3.Connection | None = None


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


def main() -> None:
    """Start the persona MCP server."""
    global _conn
    logger = configure_logging()
    data_dir = resolve_data_dir()
    _conn = init_database(data_dir)
    logger.info("Persona MCP server starting, data dir: %s", data_dir)
    mcp.run(transport="stdio")
