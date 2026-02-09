"""Configuration for persona MCP server — data directory and logging."""

import logging
import os
import sys
from pathlib import Path

DEFAULT_DATA_DIR = "~/.persona"
RESUME_SUBPATH = Path("jobs") / "resume"

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


def ensure_data_dir(data_dir: Path) -> None:
    """Ensure the data directory and jobs/resume/ structure exist."""
    resume_dir = data_dir / RESUME_SUBPATH
    resume_dir.mkdir(parents=True, exist_ok=True)


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
