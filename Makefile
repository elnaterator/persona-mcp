.PHONY: run test lint typecheck check format

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "persona-mcp — available make targets"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-20s\033[0m %s\n", $$1, $$2}'

run: ## Run the mcp server
	uv run persona

test: ## Run unit tests with pytest
	uv run pytest

lint: ## Run linter and verify formatting with ruff
	uv run ruff check . && uv run ruff format --check .

typecheck: ## Type checker
	uv run pyright

check: lint typecheck test ## Lint, type checker, and unit tests

format: ## Format code
	uv run ruff format .
