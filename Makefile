.PHONY: help up down logs test debug-db psql kind-up deploy
PYTHON ?= .venv/bin/python

help:
	@echo "up -  starts the  project"
	@echo "down - stops it"
	@echo "logs - shows the log of the backend"
	@echo "test - runs the tests of the project"
	@echo "debug-db - runs the frontend and db only"
	@echo "psql - SQL prompt in the database"
	@echo "kind-up  - create the kind cluster (if missing) and load images"
	@echo "deploy   - apply all Kubernetes manifests in k8s/"

kind-up:
	kind get clusters | grep -qx cv || kind create cluster --name cv
	docker compose build backend frontend
	kind load docker-image fastapiproject-backend:latest --name cv
	kind load docker-image fastapiproject-frontend:latest --name cv

deploy:
	kubectl apply -f k8s/

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
