# Demo Runbook

Step-by-step guide for presenting this project live.

## Prerequisites

- Docker and Docker Compose (recommended path), or
- Python 3.13 + [uv](https://docs.astral.sh/uv/) with local Mongo, MySQL, Postgres, and the mock API running

### Environment variables

The demo reads configuration from the environment. [`.env.example`](../.env.example) contains working defaults; Docker Compose loads it into the `etl` container automatically. For a local run, copy it and export the values:

```bash
cp .env.example .env
export $(grep -v '^#' .env | xargs)
```

Only these variables are required for the default demo (MySQL product source + Postgres destination). Postgres credentials use the official Docker image env vars (`POSTGRES_*`); keep `TARGET_DB_USER`, `TARGET_DB_PASSWORD`, and `TARGET_DB_DEFAULT_DATABASE` in sync with them.

| Variable | Purpose | Inside Docker (`make docker-up`) | From the host (`make verify`, Option B) |
|----------|---------|----------------------------------|----------------------------------------|
| `MONGO_URI` | Sync cursors | `mongodb://mongo:27017` | `mongodb://localhost:27017` |
| `MOCK_SOURCE_API_URL` | Orders & traffic API | `http://external-api-example:8080` | `http://localhost:8080` |
| `SOURCE_PRODUCT_BACKEND` | Product source | `mysql` | `mysql` |
| `SOURCE_MYSQL_HOST` | Product DB host | `mysql` | `localhost` |
| `SOURCE_MYSQL_PORT` | Product DB port | `3306` | `3306` |
| `SOURCE_MYSQL_USER` | Product DB user | `source` | `source` |
| `SOURCE_MYSQL_PASSWORD` | Product DB password | `source` | `source` |
| `SOURCE_MYSQL_DATABASE` | Product DB name | `marketplace_source` | `marketplace_source` |
| `POSTGRES_USER` | Postgres superuser (Docker init) | `postgres` | `postgres` |
| `POSTGRES_PASSWORD` | Postgres superuser password | `postgres` | `postgres` |
| `POSTGRES_DB` | Default Postgres database | `postgres` | `postgres` |
| `TARGET_DB_BACKEND` | Destination type | `postgres` | `postgres` |
| `TARGET_DB_HOST` | Seller DB host | `postgres` | `localhost` |
| `TARGET_DB_PORT` | Seller DB port | `5432` | `5432` |
| `TARGET_DB_USER` | Seller DB user | `postgres` (same as `POSTGRES_USER`) | `postgres` |
| `TARGET_DB_PASSWORD` | Seller DB password | `postgres` (same as `POSTGRES_PASSWORD`) | `postgres` |
| `TARGET_DB_DEFAULT_DATABASE` | Admin DB for migrations | `postgres` (same as `POSTGRES_DB`) | `postgres` |

`APP_SYNC_TYPE` and `APP_PERIODS_TO_RUN` are set by [scripts/run_e2e.sh](../scripts/run_e2e.sh) during the Docker demo; you only need them when running syncs manually (Option B). See the [Source backends](#source-backends) section if you switch `SOURCE_PRODUCT_BACKEND` to `api` or `sqlite` — then MySQL variables are not needed.

## Option A — Docker Compose (recommended)

One command starts every dependency (mock API, MongoDB, MySQL, PostgreSQL) and runs the full pipeline:

```bash
make docker-up
```

This builds the images, waits for every service to report healthy (see `healthcheck` blocks in [docker-compose.yml](../docker-compose.yml)), then runs [scripts/run_e2e.sh](../scripts/run_e2e.sh) inside the `etl` container, which:

1. Waits for Mongo, MySQL, the mock API, and Postgres to accept connections
2. Applies destination migrations (`scripts/migrate_postgres.py`)
3. Seeds seller config into MongoDB (`scripts/seed_mongo.py`)
4. Runs a **full sync** for the June 2024 window
5. Runs an **incremental sync** for the July 2024 window

### Expected output

The `etl` container logs end with a summary block per run, e.g.:

```
Starting marketplace ETL...
Processing 2 sellers
...
Marketplace ETL finished.
```

The container exits `0` when both passes complete successfully.

### Verify the results

In a second terminal, once the stack has finished the ETL run:

```bash
make verify-docker
```

This runs [scripts/verify_demo.py](../scripts/verify_demo.py) inside the Compose network using [`.env.example`](../.env.example) hostnames (`postgres`, `mongo`, …), so it checks the same Postgres instance the ETL wrote to.

Host `make verify` is for Option B only. It fails with `database "seller_a_db" does not exist` when localhost:5432 is a local Postgres install instead of the Compose container — the ETL data lives in Docker, not on your Mac's Postgres.

```
Verifying demo data (backend=postgres)

seller_a (seller_a_db):
  orders                   4 rows   [OK]
  order_payments           4 rows   [OK]
  products                 4 rows   [OK]
  traffic                  4 rows   [OK]

seller_b (seller_b_db):
  orders                   2 rows   [OK]
  order_payments           1 rows   [OK]
  products                 2 rows   [OK]
  traffic                  2 rows   [OK]

Sync dates (MongoDB seller_etl_settings):
  seller_a:
    order                2024-07-31
    order_payment        2024-07-31
    product              2024-07-31
    traffic              2024-07-31
  seller_b:
    ...

Demo verification passed: all tables populated for all sellers.
```

### Tear down

```bash
make docker-down
```

## Option B — Local run (no Docker for the ETL app)

Useful if you already have Mongo/MySQL/Postgres running locally, or want to use the SQLite backend to skip Postgres entirely.

```bash
make install
export $(grep -v '^#' .env.example | xargs)   # or copy to .env and source it
make migrate
make seed-mongo
make run-all          # first sync
make run-incremental  # incremental sync
make verify
```

For a zero-container destination, set `TARGET_DB_BACKEND=sqlite` before `make migrate` and `make run-*` — this writes to `./data/sqlite/seller_a_db.db` and `seller_b_db.db` instead of Postgres. You still need Mongo, MySQL, and the mock API reachable (Docker Compose can run just those three: `docker compose up mongo mysql external-api-example`).

### Source backends

Orders and traffic always come from the external API (`MOCK_SOURCE_API_URL`). Products are configurable via `SOURCE_PRODUCT_BACKEND`:

| Value | Products from | Extra setup |
|-------|---------------|-------------|
| `mysql` (default) | MySQL `source_products` table | `docker compose up mysql` or local MySQL with `scripts/seed_mysql.sql` |
| `sqlite` | SQLite file at `SOURCE_SQLITE_PATH` | `make seed-sqlite-source` |
| `api` | `GET /sellers/{id}/products` on the external API | No MySQL needed; API serves orders, traffic, and products |

Example — external API for all sources + Postgres destination:

```bash
SOURCE_PRODUCT_BACKEND=api make e2e
```

Example — SQLite product source + Postgres destination:

```bash
SOURCE_PRODUCT_BACKEND=sqlite make seed-sqlite-source
SOURCE_PRODUCT_BACKEND=sqlite make e2e
```


## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `etl` container exits non-zero on first run | Re-run `make docker-up` — first-time image builds plus MySQL's first boot (running `seed_mysql.sql`) can be slow; healthchecks should retry automatically, but a cold Docker cache can still be tight |
| Port already in use (5432, 3306, 27017, 8080) | Stop conflicting local services, or edit the `ports:` mappings in [docker-compose.yml](../docker-compose.yml) |
| `make verify` fails with `database "seller_a_db" does not exist` after `docker-up` | Use `make verify-docker` instead. Host `make verify` hit a different Postgres (usually a local install on port 5432). The ETL wrote seller databases inside the Compose `postgres` container. |
| `make verify` can't connect or Postgres auth fails from the host | Use `make verify-docker`, or set `TARGET_DB_HOST=localhost` (not `postgres`) and the `POSTGRES_*` / `TARGET_DB_*` credentials from [`.env.example`](../.env.example). If port 5432 is already taken by a local Postgres, stop it or remap the Compose `postgres` service port and set `TARGET_DB_PORT` to match |
| Stale data from a previous run | `docker compose down -v` removes volumes for a clean slate, then `make docker-up` again |
| Want to see it fail on purpose | Set `APP_ENTITIES_TO_RUN=doesnotexist` to demonstrate the error summary logging path |

## Related docs

- [Architecture overview](./architecture_overview.md) — why the pipeline is structured this way
- [Project structure](./project_structure.md) — where everything lives
- [Next steps](./next_steps.md) — what would come after the demo
