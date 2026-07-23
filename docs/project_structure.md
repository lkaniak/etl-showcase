# Project Structure

Tree overview of the repository. Omitted: `.venv/`, `__pycache__/`, and other generated artifacts.

```
etl-showcase/
├── README.md
├── pyproject.toml              # Workspace root (uv, pytest, import-linter)
├── uv.lock
├── .env.example                # Environment variable template
├── Dockerfile                  # ETL app container image
├── docker-compose.yml          # Full local stack (mock API, Mongo, MySQL, Postgres, ETL)
│
├── docs/
│   ├── project_overview.md     # Purpose, domain, use cases
│   ├── architecture_overview.md
│   ├── project_structure.md    # This file
│   ├── next_steps.md
│   └── agents.md               # Orientation guide for AI agents
│
├── packages/
│   └── etl/               # Generic async ETL framework (no domain, no DB drivers)
│       ├── pyproject.toml
│       └── src/
│           └── etl_core/
│               ├── config.py       # CoreSettings (shared env defaults)
│               ├── common/
│               │   ├── data/       # Date/period chunking, string helpers, pandas utils
│               │   └── logging/    # Log decorators, execution summary
│               ├── engine/
│               │   └── base_engine.py
│               ├── entities/
│               │   ├── enum/       # SyncType, log action/status enums
│               │   ├── etl_processor_entity.py
│               │   └── exceptions/
│               ├── infra/
│               │   └── concurrency/  # engine_worker, runner_worker
│               ├── modules/
│               │   └── base/       # BaseExtractor, Transformer, Loader, Processor
│               │                   # RelationalLoader (backend-agnostic load + sync dates)
│               └── ports/
│                   ├── base_etl_model.py
│                   ├── record_writer.py   # Upsert seam for destination adapters
│                   ├── sync_state_store.py
│                   └── log_sink.py
│
├── apps/
│   └── etl-usage-example/     # Marketplace domain application
│       ├── pyproject.toml
│       └── src/
│           └── my_marketplace_etl/
│               ├── main.py           # Composition root — wires adapters, runs engines
│               ├── config.py         # App settings (APP_*, TARGET_DB_*, sources)
│               ├── adapters/         # Concrete implementations of ports
│               │   ├── http/         # MockSourceApiClient (orders, traffic)
│               │   ├── mongo/        # ConfigStore, SyncStateStore
│               │   ├── mysql/        # ProductDbReader
│               │   ├── postgres/     # Connection pool, upsert SQL, RecordWriter, LoaderFactory
│               │   ├── sqlite/       # Same shape as postgres adapter
│               │   └── logging/
│               ├── ports/            # Protocol definitions (sources, LoaderFactory)
│               ├── dto/              # Pydantic source record shapes
│               ├── entities/         # Seller, ETL settings, sync dates
│               ├── models/           # SQLAlchemy destination table metadata
│               ├── engine/
│               │   └── marketplace_etl_engine.py
│               ├── modules/
│               │   ├── extractors/   # One per entity group (order, product, traffic)
│               │   ├── transformers/ # pandas cleaning + column mapping
│               │   └── processors/   # Orchestrate extract → transform → load per entity
│               └── common/data/      # Domain-specific cleaning helpers
│
├── services/
│   └── external-api-example/        # FastAPI service — mock orders & traffic HTTP API
│       ├── Dockerfile
│       ├── pyproject.toml
│       └── src/
│           └── mock_source_api/
│               └── main.py
│
├── migrations/
│   ├── postgres/001_init.sql   # Per-seller destination DDL (Postgres)
│   └── sqlite/001_init.sql     # Per-seller destination DDL (SQLite)
│
├── scripts/
│   ├── seed_mongo.py             # Seller config + empty sync cursors
│   ├── seed_mysql.sql            # Product source data (MySQL init)
│   ├── seed_sqlite_source.py     # Product source data (SQLite file)
│   ├── seed_mock_api.json        # Orders, traffic & products fixture for external API
│   ├── migrate_postgres.py       # Create seller_a_db / seller_b_db + apply DDL
│   ├── migrate_sqlite.py         # Create seller_a.db / seller_b.db + apply DDL
│   └── run_e2e.sh                # Migrate, seed, full sync, incremental sync
│
├── Makefile                      # install, test, migrate, run, e2e, docker-*
│
└── tests/
    ├── etl_core/                 # Framework tests (RelationalLoader)
    ├── adapters/
    │   ├── postgres/             # Postgres upsert SQL tests
    │   └── sqlite/               # SQLite upsert + RecordWriter tests
    └── my_marketplace_etl/
        └── transformers/         # Transformer unit tests (no Docker)
```

## Workspace members

The root `pyproject.toml` defines a **uv workspace** with three packages:

| Path | Package name | Role |
|------|--------------|------|
| `packages/etl` | `etl` | Reusable ETL framework |
| `apps/etl-usage-example` | `etl-usage-example` | Marketplace pipeline app |
| `services/external-api-example` | `external-api-example` | HTTP mock for demo sources |

## Layer responsibilities

### `packages/etl`

Backend-agnostic pipeline mechanics. Must **not** import `my_marketplace_etl` (enforced by import-linter).

- **Extract / transform / load abstractions** — base classes and the processor loop
- **RelationalLoader** — dedup, sync-date updates, delegates writes to `RecordWriter`
- **Concurrency** — parallel seller engines and entity runners
- **No DB drivers** — asyncpg and aiosqlite live in the app adapters

### `apps/etl-usage-example`

Marketplace-specific code and all external system adapters.

- **`ports/`** — what the app needs from the outside world (protocols)
- **`adapters/`** — how those needs are fulfilled (HTTP, Mongo, MySQL, Postgres, SQLite)
- **`modules/`** — ETL steps per entity: extractors, transformers, processors
- **`main.py`** — manual dependency injection; selects Postgres or SQLite backend

### `services/external-api-example`

Standalone FastAPI app serving orders and traffic from `scripts/seed_mock_api.json`. Used by Docker Compose and local runs pointing at `http://localhost:8080`.

## Data and runtime artifacts (not in repo)

| Path | Created by |
|------|------------|
| `data/sqlite/*.db` | `migrate_sqlite.py` when using SQLite backend |
| Postgres `seller_a_db`, `seller_b_db` | `migrate_postgres.py` |
| MongoDB `marketplace_etl` collections | `seed_mongo.py` + ETL sync updates |

## Related docs

- [Architecture overview](./architecture_overview.md) — why the split looks like this
- [Agent guide](./agents.md) — where to edit for common tasks
