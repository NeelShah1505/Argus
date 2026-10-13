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
	@echo "Running Argus CI Accuracy Evaluation Gates against Golden Suite..."
	$(PYTEST) evals -v

lint:
	@echo "Linting Python code"
	$(PYTHON) -m mypy packages apps/api || true
