.PHONY: help install install-dev test test-api test-new lint format clean run-server run-new-server

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package in development mode
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e ".[dev]"

test: ## Run unit tests
	pytest tests/ -v

test-api: ## Run API tests
	python test_api.py

test-new: ## Test the new simplified MCP server
	python test_new_server.py

lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/

format: ## Format code with black and isort
	black src/ tests/ tests/
	isort src/ tests/

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

setup: install-dev ## Setup development environment
	pre-commit install

check: lint test ## Run all checks (lint + test)

all: format check ## Run all checks and formatting

run-server: ## Run the original MCP server
	python src/server.py

run-new-server: ## Run the new simplified MCP server
	python run_server.py 