.PHONY: train test run batch clean install docker-build docker-up docker-down lint

# ============================================================
# ML Inference Platform Lab - Makefile
# ============================================================

PYTHON := python
PIP := pip
PYTEST := pytest
DOCKER := docker
DOCKER_COMPOSE := docker compose

# ----- Development Setup -----
install:
	$(PIP) install -r requirements.txt

# ----- Training -----
train:
	$(PYTHON) models/train_model.py

# ----- Testing -----
test:
	$(PYTEST) tests/ -v --tb=short

test-cov:
	$(PYTEST) tests/ -v --tb=short --cov=app --cov=app/services --cov=app/api --cov-report=term-missing

# ----- Run API Locally -----
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ----- Batch Scoring -----
batch:
	$(PYTHON) batch/batch_score.py --input batch/sample_input.csv --output batch/output/predictions.csv

# ----- Docker -----
docker-build:
	$(DOCKER) build -t ml-inference-platform:latest .

docker-up:
	$(DOCKER_COMPOSE) up --build -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f api

# ----- Code Quality -----
lint:
	ruff check app/ models/ batch/ tests/

format:
	ruff format app/ models/ batch/ tests/

# ----- Clean -----
clean:
	@echo "Cleaning up..."
	@rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -f batch/output/predictions.csv
	@echo "Clean complete."