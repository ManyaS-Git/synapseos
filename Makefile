# =============================================================================
# SynapseOS — Makefile
# =============================================================================
# Cross-platform task runner. Requires `make` (available on all platforms
# via Git for Windows, WSL, or native Linux/macOS).
# =============================================================================

.PHONY: install dev backend frontend docker-up docker-down lint format test clean \
        typecheck ruff black mypy check build status help

# Default target
.DEFAULT_GOAL := help

# ── Colors ────────────────────────────────────────────────────────────────────
BLUE    := \033[36m
GREEN   := \033[32m
YELLOW  := \033[33m
RED     := \033[31m
RESET   := \033[0m

# ── Install & Setup ──────────────────────────────────────────────────────────
install: ## Install all dependencies (Node.js + Python)
	@echo "$(BLUE)Installing Node.js dependencies...$(RESET)"
	npm install
	@echo "$(BLUE)Installing Python dependencies...$(RESET)"
	pip install -r apps/api/requirements.txt
	@echo "$(GREEN)All dependencies installed.$(RESET)"

install-frontend: ## Install frontend dependencies only
	npm install

install-backend: ## Install backend dependencies only
	pip install -r apps/api/requirements.txt

# ── Development ───────────────────────────────────────────────────────────────
dev: ## Start all development servers
	@echo "$(BLUE)Starting development servers...$(RESET)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(RESET)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(RESET)"
	@echo ""
	@echo "$(YELLOW)Starting API server...$(RESET)"
	cd apps/api && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

backend: ## Start backend API server only
	@echo "$(BLUE)Starting FastAPI on http://localhost:8000$(RESET)"
	cd apps/api && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start frontend dev server only
	@echo "$(BLUE)Starting Next.js on http://localhost:3000$(RESET)"
	cd apps/web && npm run dev

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up: ## Start all Docker services
	@echo "$(BLUE)Starting Docker services...$(RESET)"
	docker compose up -d
	@echo "$(GREEN)Services started. Check http://localhost:8000/docs$(RESET)"

docker-down: ## Stop all Docker services
	@echo "$(YELLOW)Stopping Docker services...$(RESET)"
	docker compose down

docker-build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(RESET)"
	docker compose build

docker-logs: ## Follow Docker service logs
	docker compose logs -f

docker-status: ## Show Docker service status
	docker compose ps

# ── Linting & Formatting ─────────────────────────────────────────────────────
lint: lint-frontend lint-backend ## Run all linters

lint-frontend: ## Lint frontend (ESLint + Prettier check)
	@echo "$(BLUE)Linting frontend...$(RESET)"
	cd apps/web && npm run lint
	@echo "$(BLUE)Checking frontend formatting...$(RESET)"
	npx prettier --check "apps/web/src/**/*.{ts,tsx,js,jsx}"

lint-backend: ## Lint backend (Ruff + Black check)
	@echo "$(BLUE)Linting backend...$(RESET)"
	cd apps/api && ruff check .
	@echo "$(BLUE)Checking backend formatting...$(RESET)"
	cd apps/api && ruff format --check .

format: format-frontend format-backend ## Format all code

format-frontend: ## Format frontend code (Prettier)
	@echo "$(BLUE)Formatting frontend...$(RESET)"
	npx prettier --write "apps/web/src/**/*.{ts,tsx,js,jsx}"

format-backend: ## Format backend code (Ruff format)
	@echo "$(BLUE)Formatting backend...$(RESET)"
	cd apps/api && ruff format .
	cd apps/api && ruff check --fix .

ruff: ## Run Ruff linter on backend
	cd apps/api && ruff check .

black: ## Run Ruff formatter (replaces Black) on backend
	cd apps/api && ruff format .

mypy: ## Run mypy type checker on backend
	@echo "$(BLUE)Running mypy...$(RESET)"
	cd apps/api && mypy app/ --ignore-missing-imports

typecheck: typecheck-frontend typecheck-backend ## Run all type checkers

typecheck-frontend: ## Type-check frontend
	cd apps/web && npm run typecheck

typecheck-backend: ## Type-check backend (mypy)
	cd apps/api && mypy app/ --ignore-missing-imports

# ── Testing ───────────────────────────────────────────────────────────────────
test: test-backend ## Run all tests

test-backend: ## Run backend tests (pytest)
	@echo "$(BLUE)Running backend tests...$(RESET)"
	cd apps/api && python -m pytest tests/ -v --tb=short

test-frontend: ## Run frontend tests
	cd apps/web && npm test

# ── Quality Checks ────────────────────────────────────────────────────────────
check: lint typecheck test ## Run all quality checks (lint + types + tests)

# ── Build ─────────────────────────────────────────────────────────────────────
build: ## Build all packages
	npm run build

build-frontend: ## Build frontend for production
	cd apps/web && npm run build

# ── Clean ─────────────────────────────────────────────────────────────────────
clean: ## Clean build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	rm -rf apps/web/.next
	rm -rf apps/web/node_modules/.cache
	rm -rf node_modules/.cache
	rm -rf apps/api/__pycache__
	rm -rf apps/api/app/__pycache__
	rm -rf apps/api/app/**/__pycache__
	rm -rf .pytest_cache
	rm -rf apps/api/.pytest_cache
	@echo "$(GREEN)Clean complete.$(RESET)"

clean-docker: ## Stop Docker and remove volumes
	docker compose down -v --remove-orphans

# ── Utilities ─────────────────────────────────────────────────────────────────
status: ## Show project status
	@echo "$(BLUE)=== SynapseOS Project Status ===$(RESET)"
	@echo ""
	@echo "$(BLUE)Docker Services:$(RESET)"
	@docker compose ps 2>/dev/null || echo "Docker not running"
	@echo ""
	@echo "$(BLUE)Python:$(RESET) $$(python --version 2>&1)"
	@echo "$(BLUE)Node:$(RESET) $$(node --version 2>&1)"
	@echo "$(BLUE)npm:$(RESET) $$(npm --version 2>&1)"

validate: ## Run the full validation script
	python scripts/validate.py

help: ## Show this help message
	@echo "$(BLUE)SynapseOS — Available Commands:$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)  %-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Usage: make <target>$(RESET)"
