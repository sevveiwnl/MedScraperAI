# MedScraperAI Development Makefile

.PHONY: help install install-dev format lint test test-cov clean docker-build docker-up docker-down pre-commit-install pre-commit-run

help: ## Show this help message
	@echo "MedScraperAI Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

format: ## Format code with black and isort
	black backend/
	isort backend/

lint: ## Run all linters
	flake8 backend/
	mypy backend/
	bandit -r backend/

lint-fix: ## Run linters and fix issues where possible
	black backend/
	isort backend/
	flake8 backend/

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term-missing

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start all services
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## View logs from all services
	docker-compose logs -f

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

setup-dev: install-dev pre-commit-install ## Setup development environment

check: format lint test ## Run all checks (format, lint, test) 