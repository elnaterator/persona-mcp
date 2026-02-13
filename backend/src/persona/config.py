"""Configuration for persona MCP server — data directory and logging."""

import logging
import os
import sys
from pathlib import Path

DEFAULT_DATA_DIR = "~/.persona"
DB_FILENAME = "persona.db"
DEFAULT_PORT = 8000

logger = logging.getLogger("persona")


def resolve_data_dir() -> Path:
    """Resolve the data directory path.

    Uses PERSONA_DATA_DIR env var if set, otherwise defaults to ~/.persona/.
    Relative paths are resolved against the current working directory.
    """
    raw = os.environ.get("PERSONA_DATA_DIR", DEFAULT_DATA_DIR)
    path = Path(raw).expanduser().resolve()
    logger.info("Data directory resolved to: %s", path)
    return path


def resolve_port() -> int:
    """Resolve the HTTP server port from PERSONA_PORT env var (default 8000)."""
    raw = os.environ.get("PERSONA_PORT", str(DEFAULT_PORT))
    return int(raw)


def resolve_cors_origins() -> list[str]:
    """Resolve CORS allowed origins from PERSONA_CORS_ORIGINS env var.

    Comma-separated list. Empty/unset = no CORS origins allowed.
    """
    raw = os.environ.get("PERSONA_CORS_ORIGINS", "")
    if not raw.strip():
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def resolve_frontend_dir() -> Path | None:
    """Resolve the frontend build directory path.

    Uses PERSONA_FRONTEND_DIR env var if set, otherwise tries to find
    frontend/dist relative to the repository root.

    Returns None if the directory doesn't exist (backend runs without frontend).
    """
    raw = os.environ.get("PERSONA_FRONTEND_DIR")

    if raw:
        # Use explicit env var if provided
        path = Path(raw).expanduser().resolve()
    else:
        # Try to find frontend/dist relative to repo root
        # The backend package is at <repo>/backend/src/persona/
        # So we go up 3 levels to get to repo root, then to frontend/dist
        try:
            repo_root = Path(__file__).parent.parent.parent.parent
            path = repo_root / "frontend" / "dist"
        except Exception:
            logger.warning("Could not determine repository root for frontend directory")
            return None

    if not path.exists():
        logger.warning(
            "Frontend directory not found: %s (backend will run without frontend)",
            path,
        )
        return None

    if not path.is_dir():
        logger.warning("Frontend path is not a directory: %s", path)
        return None

    logger.info("Frontend directory resolved to: %s", path)
    return path


def configure_logging() -> logging.Logger:
    """Configure logging to stderr with level from LOG_LEVEL env var."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    root_logger = logging.getLogger("persona")
    root_logger.setLevel(level)
    # Avoid duplicate handlers on repeated calls
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    return root_logger
