# Multi-stage build for Persona MCP server
# Stage 1: Builder - install dependencies
FROM python:3.11-slim AS builder

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Stage 2: Runtime - minimal image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY src/ /app/src/

# Set Python path and environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PERSONA_DATA_DIR=/data

# Create data directory
RUN mkdir -p /data

# Expose default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; import os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PERSONA_PORT\", \"8000\")}/health')"

# Run the server
CMD ["python", "-m", "backend.server"]
