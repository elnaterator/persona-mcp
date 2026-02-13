.PHONY: build run lint test check format help

help:
	@echo "Frontend Makefile targets:"
	@echo "  build   - Build production bundle"
	@echo "  run     - Start dev server"
	@echo "  lint    - Run ESLint"
	@echo "  test    - Run tests with Vitest"
	@echo "  check   - Run lint + test"
	@echo "  format  - Auto-format code (no formatter configured yet)"

build:
	npm run build

run:
	npm run dev

lint:
	npm run lint

test:
	npm run test

check: lint test

format:
	@echo "No formatter configured yet (consider adding prettier)"
