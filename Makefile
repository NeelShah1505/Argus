.PHONY: up down test dev lint format eval

PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

test:
	$(PYTEST) tests -v

dev:
	.venv/bin/uvicorn apps.api.main:app --reload --port 8000

eval:
	@echo "Eval harness gate: Phase 1 Golden Fixtures"
	$(PYTEST) tests -v

lint:
	@echo "Linting Python code"
	$(PYTHON) -m mypy packages apps/api || true
