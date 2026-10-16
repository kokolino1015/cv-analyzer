.PHONY: help up down logs test debug-db psql
PYTHON ?= .venv/bin/python

help:
	@echo "up -  starts the  project"
	@echo "down - stops it"
	@echo "logs - shows the log of the backend"
	@echo "test - runs the tests of the project"
	@echo "debug-db - runs the frontend and db only"
	@echo "psql - SQL prompt in the database"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f backend

test:
	cd backend && ../${PYTHON} -m pytest

debug-db:
	docker compose up -d db
	docker compose stop backend

psql:
	docker compose exec db psql -U cv cvanalyzer
