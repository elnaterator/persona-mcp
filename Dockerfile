# Multi-stage build for Persona MCP server with React frontend
# Stage 1: Frontend builder - build React SPA
FROM node:18-slim AS frontend-builder

WORKDIR /frontend

# Copy frontend dependency files
COPY frontend/package.json frontend/package-lock.json* ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build-time env var — Vite inlines VITE_* vars into the JS bundle at build time.
# Pass via: docker build --build-arg VITE_CLERK_PUBLISHABLE_KEY=pk_...
ARG VITE_CLERK_PUBLISHABLE_KEY
ENV VITE_CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLISHABLE_KEY

# Build production bundle
RUN npm run build

# Stage 2: Backend builder - install Python dependencies
FROM python:3.11-slim AS backend-builder

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy backend dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Copy backend source (needed for package installation)
COPY backend/src ./src

# Install dependencies and the persona package
RUN uv sync --frozen --no-dev

# Stage 3: Runtime - minimal image with both frontend and backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed Python dependencies from backend-builder
COPY --from=backend-builder /app/.venv /app/.venv

# Copy backend application source
COPY backend/src/ /app/src/

# Copy frontend build output
COPY --from=frontend-builder /frontend/dist /app/frontend-dist

# Set Python path and environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PERSONA_DATA_DIR=/data \
    PERSONA_FRONTEND_DIR=/app/frontend-dist

# Create data directory
RUN mkdir -p /data

# Lambda Web Adapter — bridges Lambda events to the app's localhost HTTP server
# No-op when running outside Lambda (AWS_LWA_PORT is ignored by the app directly)
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter
ENV AWS_LWA_PORT=8000

# Expose default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; import os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PERSONA_PORT\", \"8000\")}/health')"

# Run the server
CMD ["python", "-m", "persona.server"]
