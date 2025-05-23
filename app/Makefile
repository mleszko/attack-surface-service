.PHONY: run test lint format typecheck build clean

ENV_PATH ?= ./tests/cloud.json

run:
	ENV_PATH=$(ENV_PATH) uvicorn attack_surface:app --host 0.0.0.0 --port 80

test:
	pytest -v

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy .

dev: format lint typecheck test

build:
	docker build -t attack-surface .

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
