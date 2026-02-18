# Container runtime (podman or docker)
CONTAINER_RUNTIME ?= $(shell command -v podman 2>/dev/null || echo docker)

# claudelint image
CLAUDELINT_IMAGE = ghcr.io/stbenjam/claudelint:main

# AI helpers image
IMAGE_NAME ?=ai-helpers
IMAGE_TAG ?= latest
FULL_IMAGE_NAME = $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint: ## Run plugin linter, ruff syntax checker and formatter, and shellcheck
	@echo "Running claudelint with $(CONTAINER_RUNTIME)..."
	$(CONTAINER_RUNTIME) run --rm -v $(PWD):/workspace:Z ghcr.io/stbenjam/claudelint:main -v --strict
	@echo "Running ruff syntax checker on Python scripts..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
	else \
		echo "ruff not found, skipping Python syntax checking. Install with: pip install ruff"; \
		exit 1; \
	fi
	@echo "Running ruff format checker on Python scripts..."
	@ruff format --check --diff .
	@echo "Running shellcheck on shell scripts..."
	@if command -v shellcheck >/dev/null 2>&1; then \
		find . -name '*.sh' -type f -exec shellcheck {} + && echo "All checks passed!"; \
	else \
		echo "shellcheck not found, skipping shell script linting. Install with: dnf install ShellCheck"; \
		exit 1; \
	fi
	@echo "Checking that 'make update' doesn't generate uncommitted changes..."
	@$(MAKE) update
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: 'make update' generated uncommitted changes. Please commit these changes:"; \
		git status --porcelain; \
		exit 1; \
	else \
		echo "✓ No uncommitted changes after 'make update'"; \
	fi

.PHONY: update
update: ## Update Claude settings and website data
	@echo "Updating Claude settings..."
	@python3 scripts/update_claude_settings.py
	@echo "Building website data..."
	@python3 scripts/build-website.py
	@echo "Formatting Python code with ruff..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format .; \
	else \
		echo "ruff not found, skipping Python formatting. Install with: pip install ruff"; \
	fi

.PHONY: build
build: ## Build Claude container image using Containerfile
	@echo "Building Claude container image $(FULL_IMAGE_NAME) with $(CONTAINER_RUNTIME)..."
	$(CONTAINER_RUNTIME) build -f images/claude/Containerfile -t $(FULL_IMAGE_NAME) .

.PHONY: container-build
container-build: build ## Alias for build target

.PHONY: docs
docs: ## Run docs locally at http://localhost:8000
	@echo "Starting local documentation server..."
	@python3 -m http.server 8000 --directory docs

.DEFAULT_GOAL := help
