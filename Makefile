include ./deployment/docker-compose/.backend.env
include ./deployment/docker-compose/.base.env

PROJECT_NAME=exp_engine
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
ENDPOINT_URL = localhost:8000

guard-%:
	@if [ -z '${${*}}' ]; then echo 'ERROR: environment variable $* not set' && exit 1; fi

# Note: Run `make fresh-env psycopg2-binary=true` to manually replace psycopg with psycopg2-binary
fresh-env :
	conda remove --name $(PROJECT_NAME) --all -y
	conda create --name $(PROJECT_NAME) python==3.12 -y

	$(CONDA_ACTIVATE) $(PROJECT_NAME); \
	pip install -r backend/requirements.txt --ignore-installed; \
	pip install -r requirements-dev.txt --ignore-installed; \
	pre-commit install

	if [ "$(psycopg2-binary)" = "true" ]; then \
		$(CONDA_ACTIVATE) $(PROJECT_NAME); \
		pip uninstall -y psycopg2==2.9.9; \
		pip install psycopg2-binary==2.9.9; \
	fi

setup-db: guard-POSTGRES_USER guard-POSTGRES_PASSWORD guard-POSTGRES_DB
	-@docker stop pg-experiment-local
	-@docker rm pg-experiment-local
	@docker system prune -f
	@sleep 2
	@docker run --name pg-experiment-local \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD=postgres \
		-e POSTGRES_DB=postgres \
		-p 5432:5432 \
		-d postgres:16.4
	@sleep 5
	set -a && \
        source "$(CURDIR)/deployment/docker-compose/.base.env" && \
        source "$(CURDIR)/deployment/docker-compose/.backend.env" && \
        set +a && \
	cd backend && \
	python -m alembic upgrade head

teardown-db:
	@docker stop pg-experiment-local
	@docker rm pg-experiment-local
