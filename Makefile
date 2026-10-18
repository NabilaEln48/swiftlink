# Common dev commands. Run with e.g. `make test`.
.PHONY: install dev test redis-up redis-down

install:
	python -m venv .venv
	.venv/bin/pip install -e ".[dev]"

dev:
	.venv/bin/uvicorn app.main:app --reload

test:
	.venv/bin/python -m pytest -q

redis-up:
	docker compose up -d

redis-down:
	docker compose down
