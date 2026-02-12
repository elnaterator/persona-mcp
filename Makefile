.PHONY: run run-local test lint typecheck check format docker-build docker-up docker-down

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "persona-mcp — available make targets"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-20s\033[0m %s\n", $$1, $$2}'

run: ## Run the server via Docker Compose
	docker compose up --build

run-local: ## Run the server locally without Docker
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

docker-build: ## Build Docker image
	docker compose build

docker-up: ## Start Docker containers
	docker compose up -d

docker-down: ## Stop Docker containers
	docker compose down
