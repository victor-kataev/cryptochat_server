.PHONY: dev test docker_run docker_start

dev:
	@echo "==== Starting server in development environment ===="
	@uvicorn app.main:app --reload --port 8080

test:
	@echo "==== Running tests ===="
	@pytest


CONTAINER_NAME := my_postgres

docker_run:
	docker run -d --name $(CONTAINER_NAME) \
	-e POSTGRES_USER=myuser \
	-e POSTGRES_PASSWORD=mypassword \
	-e POSTGRES_DB=mydb \
	-p 5432:5432 \
	-v pgdata:/var/lib/postgresql \
	postgres:latest

docker_start:
	docker start $(CONTAINER_NAME)