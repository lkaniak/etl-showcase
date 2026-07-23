#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path

import asyncpg

MIGRATION = (Path(__file__).resolve().parents[1] / "migrations/postgres/001_init.sql").read_text()
DATABASES = ["seller_a_db", "seller_b_db"]


async def migrate(db_name: str):
    conn = await asyncpg.connect(
        host=os.getenv("TARGET_DB_HOST", "localhost"),
        port=int(os.getenv("TARGET_DB_PORT", "5432")),
        user=os.getenv("TARGET_DB_USER", "postgres"),
        password=os.getenv("TARGET_DB_PASSWORD", "postgres"),
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()

    target = await asyncpg.connect(
        host=os.getenv("TARGET_DB_HOST", "localhost"),
        port=int(os.getenv("TARGET_DB_PORT", "5432")),
        user=os.getenv("TARGET_DB_USER", "postgres"),
        password=os.getenv("TARGET_DB_PASSWORD", "postgres"),
        database=db_name,
    )
    try:
        await target.execute(MIGRATION)
        print(f"Migrated {db_name}")
    finally:
        await target.close()


async def main():
    for db in DATABASES:
        await migrate(db)


if __name__ == "__main__":
    asyncio.run(main())
