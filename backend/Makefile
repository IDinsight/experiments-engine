#!make

include ./tests/test.env
export

.PHONY : tests

# Main test target
tests: setup-test-containers run-tests teardown-test-containers

# Test runner
# NB: `pytest-alembic` requires the DB engine to point an empty database. Thus, alembic
# tests should be run first.

guard-%:
	@if [ -z "$$${*}" ]; then echo "ERROR: environment variable $* not set" && exit 1; fi

run-tests:
	python -m pytest -rPQ -m "not slow" tests

## Helper targets
setup-test-containers: setup-redis-test setup-test-db
teardown-test-containers: teardown-test-db teardown-redis-test

setup-test-db: guard-POSTGRES_PASSWORD guard-POSTGRES_USER guard-POSTGRES_DB
	-@docker stop testdb
	-@docker rm testdb
	@docker system prune -f
	@sleep 2
	@docker run --name testdb \
		-p 5433:5432 \
		-e POSTGRES_PASSWORD \
		-e POSTGRES_USER \
		-e POSTGRES_DB \
		-d postgres:16.4
	@sleep 2
	python -m alembic upgrade head
	python add_users_to_db.py

# Use port 6381 since port 6379 is used for dev and 6380 for docker-compose
setup-redis-test:
	-@docker stop redis-test
	-@docker rm redis-test
	@docker system prune -f
	@sleep 2
	@docker run --name redis-test \
		-p 6381:6379 \
		-d redis:6.0-alpine

teardown-redis-test:
	@docker stop redis-test
	@docker rm redis-test

teardown-test-db:
	@docker stop testdb
	@docker rm testdb
