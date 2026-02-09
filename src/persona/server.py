"""Persona MCP server — entry point and FastMCP setup."""

from mcp.server.fastmcp import FastMCP

from persona.config import configure_logging, ensure_data_dir, resolve_data_dir

mcp = FastMCP("persona")


def main() -> None:
    """Start the persona MCP server."""
    logger = configure_logging()
    data_dir = resolve_data_dir()
    ensure_data_dir(data_dir)
    logger.info("Persona MCP server starting, data dir: %s", data_dir)
    mcp.run(transport="stdio")
