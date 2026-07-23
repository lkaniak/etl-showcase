#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path

import aiosqlite

MIGRATION = (Path(__file__).resolve().parents[1] / "migrations/sqlite/001_init.sql").read_text()
DATABASES = ["seller_a_db", "seller_b_db"]


async def migrate(db_name: str):
    base_path = Path(os.getenv("TARGET_DB_SQLITE_BASE_PATH", "./data/sqlite"))
    base_path.mkdir(parents=True, exist_ok=True)
    db_path = base_path / f"{db_name}.db"
    conn = await aiosqlite.connect(db_path)
    try:
        await conn.executescript(MIGRATION)
        await conn.commit()
        print(f"Migrated {db_path}")
    finally:
        await conn.close()


async def main():
    for db in DATABASES:
        await migrate(db)


if __name__ == "__main__":
    asyncio.run(main())
