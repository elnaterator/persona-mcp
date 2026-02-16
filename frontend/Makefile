.PHONY: build run lint test check format install help

help:
	@echo "Frontend Makefile targets:"
	@echo "  install - Install Node.js dependencies"
	@echo "  build   - Build production bundle"
	@echo "  run     - Start dev server"
	@echo "  lint    - Run ESLint"
	@echo "  test    - Run tests with Vitest"
	@echo "  check   - Run lint + test"
	@echo "  format  - Auto-format code (no formatter configured yet)"

node_modules: package.json package-lock.json
	npm ci
	@touch node_modules

install: node_modules

build: node_modules
	npm run build

run: node_modules
	npm run dev

lint: node_modules
	npm run lint

test: node_modules
	npm run test

check: lint test

format: node_modules
	@echo "No formatter configured yet (consider adding prettier)"
