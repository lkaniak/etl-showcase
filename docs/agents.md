# Agent Guide

Quick orientation for AI agents working in this repository.

## What this repo is

Python 3.13 monorepo: a **multi-tenant marketplace ETL showcase**. Batch pipeline that extracts orders/traffic (HTTP) and products (MySQL), transforms with pandas, loads into per-seller Postgres or SQLite. Config/sync state in MongoDB.

## Repository layout

```
packages/etl/src/etl_core/   Framework — MUST stay domain- and DB-agnostic
apps/etl-usage-example/          Application — domain, processors, adapters
services/external-api-example/         FastAPI mock (orders + traffic)
scripts/                          seed_*.py, migrate_*.py, run_e2e.sh
migrations/postgres/              Destination DDL (Postgres)
migrations/sqlite/                Destination DDL (SQLite)
tests/                            pytest — transformers, loaders, upsert SQL
```

## Entry points

| Command | Purpose |
|---------|---------|
| `uv sync --all-packages` | Install workspace deps |
| `uv run pytest` | Run tests (no Docker needed for unit tests) |
| `uv run lint-imports` | Verify etl does not import app |
| `python -m my_marketplace_etl.main` | Run ETL batch job |
| `docker compose up` | Full stack e2e (Postgres backend) |
| `bash scripts/run_e2e.sh` | Wait for services, migrate, seed, run full (June) + incremental (July) sync |
| `python scripts/verify_demo.py` | Print row counts and sync dates to confirm a run succeeded |
| `make demo` | `e2e` + `verify` in one command |

## Key files to read first

| File | Why |
|------|-----|
| `apps/.../main.py` | Composition root — wires adapters, creates engines per seller |
| `apps/.../engine/marketplace_etl_engine.py` | Configures processors per entity/sync type |
| `apps/.../config.py` | All env settings (`APP_*`, `TARGET_DB_*`, source URLs) |
| `packages/etl/src/etl_core/modules/base/base_processor.py` | Extract → transform → load loop |
| `packages/etl/src/etl_core/modules/base/relational_loader.py` | Backend-agnostic load + sync dates |
| `apps/.../ports/` | Protocol definitions (sources, LoaderFactory) |
| `apps/.../adapters/postgres/` and `adapters/sqlite/` | Dialect-specific upsert + RecordWriter |

## Architecture rules (do not break)

1. **`etl` must not import `my_marketplace_etl`** — enforced by import-linter
2. **No DB drivers in etl** — asyncpg/aiosqlite live in app adapters only
3. **Dialect-specific SQL stays in adapters** — `build_upsert_query` is not framework code
4. **Processors depend on protocols** — `LoaderFactory`, source protocols, not concrete pools
5. **Do not add code comments** unless the user explicitly asks

## Data flow (one seller, one entity)

```
main.py
  → MarketplaceEtlEngine.configure()
    → OrderProcessor / ProductProcessor / TrafficProcessor
      → Extractor.extract()          # calls source protocol
      → Transformer.transform()      # pandas → dicts
      → RelationalLoader.load()      # dedup → RecordWriter.upsert_records()
      → SyncStateStore.update_sync_dates()
```

## Ports and their default adapters

| Port | Location | Default adapter |
|------|----------|-----------------|
| `OrderSourceClient` | `ports/order_source.py` | `adapters/http/mock_source_api_client.py` |
| `TrafficSourceClient` | `ports/traffic_source.py` | same HTTP client |
| `ProductDbReader` | `ports/product_db_reader.py` | `adapters/mysql/`, `adapters/sqlite/`, or `adapters/http/` (`fetch_products`) |
| `ConfigStore` | `ports/config_store.py` | `adapters/mongo/mongo_repositories.py` |
| `SyncStateStore` | `etl_core/ports/sync_state_store.py` | `MongoSyncStateStore` |
| `LoaderFactory` | `ports/loader_factory.py` | `adapters/postgres/` or `adapters/sqlite/` |
| `RecordWriter` | `etl_core/ports/record_writer.py` | Postgres/Sqlite record writers |

## Environment variables (common)

See `.env.example`. Critical ones:

- `TARGET_DB_BACKEND` — `postgres` (default) or `sqlite`
- `SOURCE_PRODUCT_BACKEND` — `mysql` (default), `sqlite`, or `api`
- `APP_SYNC_TYPE` — `all`, `first`, or `incremental`
- `APP_ENTITIES_TO_RUN` — comma-separated: `order,product,traffic`
- `APP_PERIODS_TO_RUN` — optional fixed window: `2024-06-01,2024-06-30`
- `MONGO_URI`, `MOCK_SOURCE_API_URL`, `SOURCE_MYSQL_*`, `SOURCE_SQLITE_PATH`, `TARGET_DB_*`

## Entities and processors

| Entity key | Processor | Models loaded |
|------------|-----------|---------------|
| `order` | `OrderProcessor` | `OrderModel`, `OrderPaymentModel` |
| `product` | `ProductProcessor` | `ProductModel` |
| `traffic` | `TrafficProcessor` | `TrafficModel` |

Dependencies (`marketplace_dependencies`): order → order_payment. `ProductModel` carries catalog and stock fields together (there is no separate performance model).

## Where to make common changes

| Task | Where to edit |
|------|---------------|
| Add a new entity | Model in `models/`, extractor/transformer/processor, register in `processors/__init__.py`, migration SQL |
| Add a new source | New port + adapter in `adapters/`, wire in engine `configure()` |
| Add a DB backend | New `adapters/<backend>/` with upsert_query, record_writer, loader_factory; branch in `main.py` |
| Change upsert behavior | Backend adapter's `record_writer.py` and `upsert_query.py` |
| Change sync date logic | `relational_loader.py` (core) or Mongo adapter |
| Add unit tests | `tests/` — prefer testing transformers and upsert SQL without Docker |

## Testing notes

- Transformer tests: `tests/my_marketplace_etl/transformers/`
- Loader tests: `tests/etl_core/test_relational_loader.py`
- Upsert SQL tests: `tests/adapters/postgres/`, `tests/adapters/sqlite/`
- Full e2e requires Docker Compose (Mongo, MySQL, Postgres, mock API) unless using SQLite backend with local services

## Docs map

- [demo.md](./demo.md) — presenter runbook for a live demo
- [project_overview.md](./project_overview.md) — purpose and use cases
- [architecture_overview.md](./architecture_overview.md) — design decisions, trade-offs, limitations
- [project_structure.md](./project_structure.md) — directory tree and layer responsibilities
- [next_steps.md](./next_steps.md) — improvement ideas

## Pitfalls

- Processors take `LoaderFactory`, not `asyncpg.Pool` — do not reintroduce pool types into processors
- `RelationalLoader` uses `tenant_id: str`, not `SellerEntity` — keeps etl app-agnostic
- Custom update routine `ignore_columns_to_update_on_upsert` is keyed by `repr()` matching `"ignore_columns_to_update_on_upsert"` — see `APP_CUSTOM_UPDATE_ROUTINE` in config
- Per-seller destination: Postgres database name or `{TARGET_DB_SQLITE_BASE_PATH}/{relational_database_name}.db`
