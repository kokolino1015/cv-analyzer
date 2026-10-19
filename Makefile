.PHONY: help up down logs test debug-db psql kind-up deploy forward stop-forward redeploy
PYTHON ?= .venv/bin/python
PORT_FORWARD_BACKEND_LOG := /tmp/fastapi-port-forward-backend.log
PORT_FORWARD_FRONTEND_LOG := /tmp/fastapi-port-forward-frontend.log
PID_BACKEND_FILE ?= /tmp/fastapi-backend.pid
PID_FRONTEND_FILE ?= /tmp/fastapi-frontend.pid

help:
	@echo "Docker Compose (local, ports 3000 / 8000)"
	@echo "  make up            start db, backend and frontend in Docker"
	@echo "  make down          stop the containers (data is kept)"
	@echo "  make logs          follow the backend's logs"
	@echo "  make test          run the pytest suite with the venv's Python"
	@echo "  make debug-db      start only the db, for debugging the backend in PyCharm"
	@echo "  make psql          open a SQL prompt in the Compose database"
	@echo ""
	@echo "Kubernetes (kind cluster 'cv', ports 3001 / 8001)"
	@echo "  make kind-up       create the cluster if missing, build and load the images"
	@echo "  make deploy        apply every manifest in k8s/"
	@echo "  make redeploy      rebuild, restart backend + frontend, wait, reopen the tunnels"
	@echo "  make forward       open tunnels: app on localhost:3001, API on localhost:8001"
	@echo "  make stop-forward  close the tunnels"

redeploy: kind-up deploy
	kubectl rollout restart deploy/backend deploy/frontend
	kubectl rollout status deploy/backend
	kubectl rollout status deploy/frontend
	@$(MAKE) --no-print-directory stop-forward
	@$(MAKE) --no-print-directory forward
	@echo "Ready: app http://localhost:3001  |  API docs http://localhost:8001/docs"

forward:
	@nohup kubectl port-forward svc/frontend 3001:80 >$(PORT_FORWARD_FRONTEND_LOG) 2>&1 & echo $$! > $(PID_FRONTEND_FILE)
	
	@nohup kubectl port-forward svc/backend 8001:8000 >$(PORT_FORWARD_BACKEND_LOG) 2>&1 & echo $$! > $(PID_BACKEND_FILE)

stop-forward:
	@if [ -s ${PID_BACKEND_FILE} ]; then \
	kill $$(cat $(PID_BACKEND_FILE)) 2>/dev/null || true; \
	fi
	@rm -f $(PID_BACKEND_FILE)

	@if [ -s ${PID_FRONTEND_FILE} ]; then \
        kill $$(cat $(PID_FRONTEND_FILE)) 2>/dev/null || true; \
	fi
	@rm -f $(PID_FRONTEND_FILE)

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
