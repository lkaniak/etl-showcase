.DEFAULT_GOAL := help

UV := uv
RUN := $(UV) run

.PHONY: help install test lint-imports \
	seed-mongo seed-sqlite-source migrate-postgres migrate-sqlite migrate \
	run run-all run-incremental e2e verify verify-docker demo \
	docker-up docker-down docker-build

help: ## Show available targets
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install: ## Install workspace dependencies (uv sync)
	$(UV) sync --all-packages

test: ## Run pytest
	$(RUN) pytest

lint-imports: ## Verify etl does not import the app
	$(RUN) lint-imports

seed-mongo: ## Seed MongoDB seller config and sync cursors
	$(RUN) python scripts/seed_mongo.py

seed-sqlite-source: ## Seed SQLite product source database
	$(RUN) python scripts/seed_sqlite_source.py

migrate-postgres: ## Create seller DBs and apply Postgres migrations
	$(RUN) python scripts/migrate_postgres.py

migrate-sqlite: ## Create seller DB files and apply SQLite migrations
	$(RUN) python scripts/migrate_sqlite.py

migrate: ## Run migration for TARGET_DB_BACKEND (postgres or sqlite)
	@if [ "$${TARGET_DB_BACKEND:-postgres}" = "sqlite" ]; then \
		$(MAKE) migrate-sqlite; \
	else \
		$(MAKE) migrate-postgres; \
	fi

run: ## Run ETL (respects APP_SYNC_TYPE and other env vars)
	$(RUN) python -m my_marketplace_etl.main

run-all: ## Run ETL with APP_SYNC_TYPE=all
	APP_SYNC_TYPE=all $(RUN) python -m my_marketplace_etl.main

run-incremental: ## Run ETL with APP_SYNC_TYPE=incremental
	APP_SYNC_TYPE=incremental $(RUN) python -m my_marketplace_etl.main

e2e: ## Migrate, seed, full sync, then incremental sync
	bash scripts/run_e2e.sh

verify: ## Verify demo data from the host (requires env pointing at the same Postgres as the ETL)
	$(RUN) python scripts/verify_demo.py

verify-docker: ## Verify demo data via the Compose network (recommended after docker-up)
	docker compose run --rm --no-deps etl python scripts/verify_demo.py

demo: ## Run the full e2e pipeline and verify the results
	$(MAKE) e2e
	$(MAKE) verify

docker-up: ## Start full stack with Docker Compose
	docker compose up --build

docker-down: ## Stop Docker Compose stack
	docker compose down

docker-build: ## Build Docker images without starting
	docker compose build
