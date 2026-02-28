.PHONY: build run lint test typecheck check format help
unexport VIRTUAL_ENV

help:
	@echo "Backend Makefile targets:"
	@echo "  build     - Install Python dependencies"
	@echo "  run       - Start HTTP server locally"
	@echo "  lint      - Run ruff check + format check + pyright"
	@echo "  test      - Run pytest"
	@echo "  typecheck - Run pyright"
	@echo "  check     - Run lint + typecheck + test"
	@echo "  format    - Auto-format with ruff"

build:
	uv sync

run:
	uv run persona

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright

test:
	uv run pytest

typecheck:
	uv run pyright

check: lint test

format:
	uv run ruff format .
