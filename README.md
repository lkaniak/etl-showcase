# etl-showcase

Multi-tenant marketplace ETL pipeline in Python — a reference implementation for extract-transform-load architecture with ports/adapters, incremental sync, and swappable destination backends (Postgres or SQLite).

## Quick start

**Requirements:** Python 3.13, [uv](https://docs.astral.sh/uv/)

```bash
make install
make test
```

Or directly:

```bash
uv sync --all-packages
uv run pytest
```

**Full stack (Docker):**

```bash
make docker-up
```

Or:

```bash
docker compose up
```

Copy `.env.example` to `.env` and adjust as needed. See [docs/project_overview.md](docs/project_overview.md) for manual setup without Docker.

**Run the ETL:**

```bash
make seed-mongo migrate run
```

Or step by step:

```bash
python scripts/seed_mongo.py
python scripts/migrate_postgres.py   # or: make migrate-sqlite with TARGET_DB_BACKEND=sqlite
python -m my_marketplace_etl.main
```

Run `make help` for all targets (e2e, lint-imports, run-all, etc.).

## Documentation

- [Demo runbook](docs/demo.md) — step-by-step guide for presenting this project live
- [Project overview](docs/project_overview.md) — what it solves and use-case ideas
- [Architecture overview](docs/architecture_overview.md) — design decisions, ecosystem fit, trade-offs, limitations
- [Project structure](docs/project_structure.md) — directory tree and layer responsibilities
- [Next steps](docs/next_steps.md) — improvement paths
- [Agent guide](docs/agents.md) — repo orientation for AI assistants

## Structure

```
packages/etl/          Generic ETL framework
apps/etl-usage-example/    Marketplace application
services/external-api-example/   Mock orders/traffic API
```

## License

[MIT](LICENSE)
