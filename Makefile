include ./deployment/docker-compose/.backend.env
include ./deployment/docker-compose/.base.env

PROJECT_NAME=exp_engine
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
ENDPOINT_URL = localhost:8000

guard-%:
	@if [ -z '${${*}}' ]; then echo 'ERROR: environment variable $* not set' && exit 1; fi

# Note: Run `make fresh-env psycopg2-binary=true` to manually replace psycopg with psycopg2-binary
fresh-env:
	@if conda env list | grep -q "$(PROJECT_NAME)"; then \
		conda remove --name $(PROJECT_NAME) --all -y; \
	fi
	conda create --name $(PROJECT_NAME) python==3.12 -y

	$(CONDA_ACTIVATE) $(PROJECT_NAME); \
	pip install -r backend/requirements.txt --ignore-installed; \
	pip install -r requirements-dev.txt --ignore-installed; \
	pip install -r requirements-docs.txt --ignore-installed; \
	pre-commit install

	if [ "$(psycopg2-binary)" = "true" ]; then \
		$(CONDA_ACTIVATE) $(PROJECT_NAME); \
		pip uninstall -y psycopg2==2.9.9; \
		pip install psycopg2-binary==2.9.9; \
	fi

	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# --- Local development commands ---
setup-dev: setup-redis setup-db

setup-db: guard-POSTGRES_USER guard-POSTGRES_PASSWORD guard-POSTGRES_DB
	-@docker stop pg-experiment-local
	-@docker rm pg-experiment-local
	@docker system prune -f
	@sleep 2
	@docker run --name pg-experiment-local \
		-e POSTGRES_USER=$(POSTGRES_USER) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		-e POSTGRES_DB=$(POSTGRES_DB) \
		-p 5432:5432 \
		-d postgres:16.4
	@sleep 5
	set -a && \
        source "$(CURDIR)/deployment/docker-compose/.base.env" && \
        source "$(CURDIR)/deployment/docker-compose/.backend.env" && \
        set +a && \
	cd backend && \
	python -m alembic upgrade head
	python backend/add_users_to_db.py

teardown-db:
	@docker stop pg-experiment-local
	@docker rm pg-experiment-local

setup-redis:
	-@docker stop redis-experiment-local
	-@docker rm redis-experiment-local
	@docker system prune -f
	@sleep 2
	@docker run --name redis-experiment-local \
     -p 6379:6379 \
     -d redis:6.0-alpine

teardown-redis:
	@docker stop redis-experiment-local
	@docker rm redis-experiment-local


run-backend:
	$(CONDA_ACTIVATE) $(PROJECT_NAME); \
	make setup-redis && make setup-db && \
	sleep 5 && \
	set -a && \
        source "$(CURDIR)/deployment/docker-compose/.base.env" && \
        source "$(CURDIR)/deployment/docker-compose/.backend.env" && \
  set +a && \
	python backend/main.py

run-frontend:
	cd frontend && npm run dev


# --- Prod instance (with no hot reload) commands, use for deployment ---
server-start:
	cd deployment/docker-compose && docker-compose -f docker-compose.yml -p exe-prod up --build -d --remove-orphans

server-stop:
	cd deployment/docker-compose && docker-compose -f docker-compose.yml -p exe-prod down

server-restart:
	cd deployment/docker-compose && docker-compose -f docker-compose.yml -p exe-prod restart

server-status:
	cd deployment/docker-compose && docker-compose ps

server-prune:
	cd deployment/docker-compose && docker system prune -f --force

server-soft-reset: # delete all containers and images
	make server-stop
	make server-prune
	make server-start

# -- Dev instance (with hot reload) commands ---
dev-inst-start:
	cd deployment/docker-compose && docker-compose -f docker-compose-dev.yml -p exe-dev up --build -d --remove-orphans

dev-inst-stop:
	cd deployment/docker-compose && docker-compose -f docker-compose-dev.yml -p exe-dev down

dev-inst-restart:
	cd deployment/docker-compose && docker-compose -f docker-compose-dev.yml -p exe-dev restart

dev-inst-soft-reset: # delete all containers and images
	make dev-inst-stop
	make server-prune
	make dev-inst-start

dev-inst-hard-reset: # delete all containers, images and volumes
	make dev-inst-stop
	@docker system prune -f --volumes --force
	make dev-inst-start
