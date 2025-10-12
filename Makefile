dev:
	@echo "==== Starting server in development environment ===="
	@uvicorn app.main:app --reload --port 8080

test:
	@echo "==== Running tests ===="
	@pytest
