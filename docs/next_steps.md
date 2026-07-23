# Next Steps

Possible improvements grouped by the limitations described in [architecture_overview.md](./architecture_overview.md).

## Operational maturity

- **Add a scheduler integration** — wrap `python -m my_marketplace_etl.main` in a Prefect flow, Airflow DAG, or K8s CronJob; pass `APP_SYNC_TYPE` and `APP_SELLERS_TO_RUN` as run parameters
- **Dead-letter / retry queue** — persist failed seller runs to a queue collection; add a reaper script that retries with exponential backoff beyond the current in-loader retry
- **Structured observability** — implement `LogSink` (port exists in etl) with OpenTelemetry or JSON stdout; emit per-seller, per-entity metrics (rows loaded, duration, errors)
- **Health checks** — expose readiness endpoints on the mock API pattern for each dependency before the ETL starts (extend `run_e2e.sh` logic into a reusable preflight module)

## Config and state abstraction

- **In-memory `ConfigStore` / `SyncStateStore`** — enable full pipeline tests without MongoDB; useful for CI and local dev with SQLite destination
- **Env-driven adapter registry** — replace the `if TARGET_DB_BACKEND` branch in `main.py` with a small factory map so adding backends doesn't touch the composition root
- **File-based config** — YAML/JSON seller definitions as an alternative to Mongo for simpler deployments

## Source adapters

- **In-memory / fixture `ProductDbReader`** — return canned DTOs for processor integration tests
- **Additional source types** — S3 parquet reader, webhook buffer, or Kafka consumer implementing the existing source protocols
- **Unified source factory** — mirror `LoaderFactory` on the extraction side so processors don't branch on entity type in the engine

## Destination and loading

- **Consolidate custom update routines** — extract shared row-filtering logic; inject only the dialect-specific `build_upsert_query` into Postgres and SQLite writers
- **Add warehouse adapters** — BigQuery/Snowflake `RecordWriter` implementations using bulk load APIs
- **Alembic or sqlx migrations** — generate migrations from SQLAlchemy models to reduce hand-written SQL drift
- **Connection pool abstraction** — optional shared `DbConnectionPool` protocol if a third SQL backend is added and duplication grows

## Sync semantics

- **Watermark / CDC mode** — track high-water marks per source instead of calendar-date chunks; support late-arriving records with merge keys
- **Idempotency keys** — store run IDs and reject duplicate loads for the same period
- **Entity dependency graph** — generalize `marketplace_dependencies` into a declarable DAG rather than a hardcoded dict

## Testing and CI

- **Full pipeline integration test** — in-memory config + SQLite destination + fixture sources; run one seller end-to-end in pytest without Docker
- **Docker Compose profiles** — `sqlite` profile that drops Postgres and sets `TARGET_DB_BACKEND=sqlite`
- **Contract tests for mock API** — verify mock source responses match `OrderRecord` / `TrafficRecord` schemas

## Developer experience

- **CLI with subcommands** — `marketplace-etl run`, `marketplace-etl migrate`, `marketplace-etl seed` instead of separate scripts
- **Second example app** — a minimal `apps/other-etl/` consuming `etl` to prove the framework split
- **Architecture decision records (ADRs)** — document why ports/adapters were chosen over a heavier framework

## Scalability (if moving toward production)

- **Distributed worker model** — publish seller jobs to a queue (SQS, Redis); workers pull and run a single `MarketplaceEtlEngine`
- **Shared destination with row-level tenancy** — alternative to per-seller DBs if operational overhead of many databases is too high
- **Rate limiting on sources** — respect API quotas in extractors with token buckets per seller
