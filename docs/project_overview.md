# Project Overview

A reference implementation of a **multi-tenant marketplace ETL pipeline** in Python. It syncs seller data from heterogeneous sources into per-seller analytical databases, with support for full, first-time, and incremental runs.

This is a **showcase project**: the domain (marketplace sellers, orders, products, traffic) is realistic enough to force real design decisions, but the data sources are mocked so the repo runs locally without external dependencies.

## What it solves

Marketplace analytics teams typically need to:

- Pull data from **multiple source systems** (APIs, operational DBs) with different shapes and cadences
- **Normalize and clean** records before loading
- Write into **tenant-isolated** destination databases (one DB per seller)
- Track **sync state** per entity so incremental runs only fetch what changed
- Run **many sellers in parallel** without one failure blocking the rest

This project demonstrates how to structure that pipeline as maintainable, testable Python — with clear boundaries between generic ETL mechanics and marketplace-specific logic.

## Domain model

| Entity | Source | Destination |
|--------|--------|-------------|
| Orders, order payments | Mock HTTP API | PostgreSQL / SQLite (per seller) |
| Traffic | Mock HTTP API | PostgreSQL / SQLite (per seller) |
| Products (catalog + stock) | MySQL | PostgreSQL / SQLite (per seller) |

Configuration and sync cursors live in **MongoDB**. Two mock sellers (`seller_a`, `seller_b`) ship with seed data.

## Use-case ideas

- **Learning ETL architecture** — study ports/adapters, extract-transform-load separation, and incremental sync patterns without a production codebase's noise
- **Onboarding template** — fork the monorepo layout (`etl` + app + services) when starting a new data pipeline team
- **Adapter prototyping** — add a new source (e.g. S3, Kafka) or destination backend by implementing the existing protocols
- **Local integration testing** — run the full stack via Docker Compose or swap Postgres for SQLite when you don't want containers
- **Concurrency experiments** — tune `MAX_RUNNER_EXECUTIONS` and per-processor timeouts to explore parallel seller processing
- **CI fixture** — use the mock API + in-memory/in-file SQLite as a fast, deterministic ETL smoke test in pipelines

## What this is not

- A production-ready orchestrator (Airflow, Dagster, etc.) — it is a batch script that exits when done
- A streaming or CDC pipeline — sync is date-range batch extraction
- A managed marketplace product — all external systems are mocks or local containers
