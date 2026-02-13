.PHONY: build run lint test typecheck check format help

help:
	@echo "Backend Makefile targets:"
	@echo "  build     - Install Python dependencies"
	@echo "  run       - Start HTTP server locally"
	@echo "  lint      - Run ruff check + format check"
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

test:
	uv run pytest

typecheck:
	uv run pyright

check: lint typecheck test

format:
	uv run ruff format .
