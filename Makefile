.PHONY: run test lint typecheck check format

run:
	uv run persona

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check .

typecheck:
	uv run pyright

check: lint typecheck test

format:
	uv run ruff format .
