.PHONY: help setup dev test test-backend test-frontend lint format build docker-up docker-down models demo wipe-data

PYTHON ?= python
NPM ?= npm

help:
	@echo "C.O.P.P.E.R. Makefile targets:"
	@echo "  setup         Install backend and frontend dependencies"
	@echo "  dev           Start development servers (backend & frontend)"
	@echo "  test          Run all tests (backend pytest + frontend vitest)"
	@echo "  test-backend  Run backend pytest test suite"
	@echo "  test-frontend Run frontend vitest test suite"
	@echo "  lint          Run code linters (ruff & oxlint)"
	@echo "  format        Format code (ruff format)"
	@echo "  build         Build frontend assets"
	@echo "  docker-up     Start services via docker-compose"
	@echo "  docker-down   Stop services via docker-compose"
	@echo "  models        Verify and provision local Ollama models"
	@echo "  demo          Launch standalone offline demo mode"
	@echo "  wipe-data     Purge all local runtime state and databases"

setup:
	$(PYTHON) -m pip install -e .
	cd frontend && $(NPM) install

dev:
	$(PYTHON) scripts/dev/run_dev.py

test: test-backend test-frontend

test-backend:
	$(PYTHON) -m pytest tests/ -q

test-frontend:
	cd frontend && $(NPM) run test

lint:
	$(PYTHON) -m ruff check --config pyproject.toml .
	cd frontend && $(NPM) run lint

format:
	$(PYTHON) -m ruff format --config pyproject.toml .

build:
	cd frontend && $(NPM) run build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

models:
	$(PYTHON) scripts/models/ensure_ollama_models.py

demo:
	$(PYTHON) -c "import os; os.environ['COPPER_DEMO']='1'; import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)"

wipe-data:
	$(PYTHON) scripts/wipe_data.py --all
