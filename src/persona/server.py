"""Persona MCP server — entry point and FastMCP setup."""

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from persona.config import configure_logging, ensure_data_dir, resolve_data_dir
from persona.tools import read as read_tools
from persona.tools import write as write_tools

mcp = FastMCP("persona")

# Resolved at startup in main(), used by tool handlers.
_data_dir: Path = Path()


@mcp.tool()
def get_resume() -> dict[str, Any]:
    """Get the full resume as structured data.

    Returns contact info, summary, experience, education, and skills.
    """
    return read_tools.get_resume(data_dir=_data_dir)


@mcp.tool()
def get_resume_section(section: str) -> Any:
    """Get a specific resume section by name.

    Args:
        section: One of: contact, summary, experience, education, skills.
    """
    return read_tools.get_resume_section(section=section, data_dir=_data_dir)


@mcp.tool()
def update_section(section: str, data: dict[str, Any]) -> str:
    """Update a non-list resume section (contact info or summary).

    Args:
        section: One of: contact, summary.
        data: Fields to update. For contact: any subset of contact fields.
              For summary: {"text": "new summary"}.
    """
    return write_tools.update_section(section=section, data=data, data_dir=_data_dir)


@mcp.tool()
def add_entry(section: str, data: dict[str, Any]) -> str:
    """Add an entry to a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        data: Entry fields. Required fields vary by section.
    """
    return write_tools.add_entry(section=section, data=data, data_dir=_data_dir)


@mcp.tool()
def update_entry(section: str, index: int, data: dict[str, Any]) -> str:
    """Update an existing entry in a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        index: 0-based index of the entry to update.
        data: Fields to update (partial update, omitted fields unchanged).
    """
    return write_tools.update_entry(
        section=section, index=index, data=data, data_dir=_data_dir
    )


@mcp.tool()
def remove_entry(section: str, index: int) -> str:
    """Remove an entry from a list-based resume section.

    Args:
        section: One of: experience, education, skills.
        index: 0-based index of the entry to remove.
    """
    return write_tools.remove_entry(section=section, index=index, data_dir=_data_dir)


def main() -> None:
    """Start the persona MCP server."""
    global _data_dir
    logger = configure_logging()
    _data_dir = resolve_data_dir()
    ensure_data_dir(_data_dir)
    logger.info("Persona MCP server starting, data dir: %s", _data_dir)
    mcp.run(transport="stdio")
