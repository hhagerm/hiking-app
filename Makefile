COMPOSE_TEST := docker compose -f docker-compose.test.yml

.PHONY: test-db test-db-down test

test-db:
	$(COMPOSE_TEST) up -d --wait db-test
	$(COMPOSE_TEST) run --rm migrator

test-db-down:
	$(COMPOSE_TEST) down -v

test:
	uv run pytest
