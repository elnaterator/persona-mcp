.PHONY: build run run-local lint test check format tf-lint tf-check setup help

help:
	@echo "Root Makefile targets:"
	@echo "  setup      - Install all managed dependencies (Python + Node)"
	@echo "  build      - Build frontend then backend"
	@echo "  run        - Start via Docker Compose"
	@echo "  run-local  - Build frontend then run backend locally"
	@echo "  lint       - Lint both frontend and backend"
	@echo "  test       - Test both frontend and backend"
	@echo "  check      - Run lint + test for both + terraform fmt check"
	@echo "  format     - Format both frontend and backend"
	@echo "  tf-lint    - Check Terraform formatting (infra/)"
	@echo "  tf-check   - tf-lint + Checkov security scan (infra/)"

setup:
	cd backend && uv sync
	cd frontend && npm ci

build:
	$(MAKE) -C frontend build
	$(MAKE) -C backend build

run:
	docker compose up --build

run-local:
	$(MAKE) -C frontend build
	$(MAKE) -C backend run

lint:
	$(MAKE) -C frontend lint
	$(MAKE) -C backend lint

test:
	$(MAKE) -C frontend test
	$(MAKE) -C backend test

check:
	$(MAKE) -C frontend check
	$(MAKE) -C backend check
	$(MAKE) tf-lint

format:
	$(MAKE) -C frontend format
	$(MAKE) -C backend format

tf-lint:
	terraform fmt -check -recursive infra/

tf-check:
	$(MAKE) tf-lint
	uvx checkov -d infra/ --quiet --compact
