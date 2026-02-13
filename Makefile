.PHONY: build run run-local lint test check format help

help:
	@echo "Root Makefile targets:"
	@echo "  build      - Build frontend then backend"
	@echo "  run        - Start via Docker Compose"
	@echo "  run-local  - Build frontend then run backend locally"
	@echo "  lint       - Lint both frontend and backend"
	@echo "  test       - Test both frontend and backend"
	@echo "  check      - Run lint + test for both"
	@echo "  format     - Format both frontend and backend"

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

format:
	$(MAKE) -C frontend format
	$(MAKE) -C backend format
