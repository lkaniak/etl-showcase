#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

TABLES = ["orders", "order_payments", "products", "traffic"]
SELLERS = [
    ("seller_a", "seller_a_db"),
    ("seller_b", "seller_b_db"),
]


def _postgres_target() -> tuple[str, int, str, str]:
    return (
        os.getenv("TARGET_DB_HOST", "localhost"),
        int(os.getenv("TARGET_DB_PORT", "5432")),
        os.getenv("TARGET_DB_USER", "postgres"),
        os.getenv("TARGET_DB_PASSWORD", "postgres"),
    )


async def _postgres_catalog() -> list[str]:
    import asyncpg

    host, port, user, password = _postgres_target()
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database="postgres",
    )
    try:
        rows = await conn.fetch(
            "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
        )
        return [row["datname"] for row in rows]
    finally:
        await conn.close()


async def count_postgres(db_name: str) -> dict[str, int]:
    import asyncpg

    host, port, user, password = _postgres_target()
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
        )
    except asyncpg.InvalidCatalogNameError:
        catalogs = await _postgres_catalog()
        raise SystemExit(
            "\n".join(
                [
                    f'Postgres database "{db_name}" does not exist at {host}:{port}.',
                    f"Databases on that server: {', '.join(catalogs) or '(none)'}",
                    "After `make docker-up`, run `make verify-docker` to check the Compose Postgres.",
                    "Host `make verify` only works if localhost:5432 is the Compose Postgres, not a local install.",
                ]
            )
        ) from None
    except (asyncpg.InvalidPasswordError, OSError) as exc:
        hint = (
            "After `make docker-up`, run `make verify-docker`."
            if host in {"localhost", "127.0.0.1", "postgres"}
            else "Check TARGET_DB_HOST, TARGET_DB_PORT, and POSTGRES_* credentials."
        )
        raise SystemExit(
            f"Could not connect to Postgres at {host}:{port} as {user}: {exc}\n{hint}"
        ) from None
    try:
        counts = {}
        for table in TABLES:
            counts[table] = await conn.fetchval(f'SELECT COUNT(*) FROM "{table}"')
        return counts
    finally:
        await conn.close()


async def count_sqlite(db_name: str) -> dict[str, int]:
    import aiosqlite

    base_path = Path(os.getenv("TARGET_DB_SQLITE_BASE_PATH", "./data/sqlite"))
    db_path = base_path / f"{db_name}.db"
    if not db_path.exists():
        return {table: 0 for table in TABLES}
    counts = {}
    async with aiosqlite.connect(db_path) as conn:
        for table in TABLES:
            cursor = await conn.execute(f"SELECT COUNT(*) FROM {table}")
            row = await cursor.fetchone()
            counts[table] = row[0] if row else 0
    return counts


def print_sync_dates() -> None:
    from pymongo import MongoClient

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DATABASE_NAME", "marketplace_etl")
    client = MongoClient(mongo_uri)
    db = client[mongo_db_name]

    print("Sync dates (MongoDB seller_etl_settings):")
    for seller_id, _ in SELLERS:
        doc = db.seller_etl_settings.find_one({"seller_id": seller_id}) or {}
        sync_dates = doc.get("sync_dates", {})
        print(f"  {seller_id}:")
        if not sync_dates:
            print("    (no sync dates recorded)")
            continue
        for entity, date in sorted(sync_dates.items()):
            print(f"    {entity:<20} {date or '(never synced)'}")


async def main() -> int:
    backend = os.getenv("TARGET_DB_BACKEND", "postgres")
    print(f"Verifying demo data (backend={backend})\n")

    all_ok = True
    for seller_id, db_name in SELLERS:
        counts = await count_sqlite(db_name) if backend == "sqlite" else await count_postgres(db_name)
        print(f"{seller_id} ({db_name}):")
        for table, count in counts.items():
            ok = count > 0
            all_ok = all_ok and ok
            marker = "OK" if ok else "EMPTY"
            print(f"  {table:<20} {count:>5} rows   [{marker}]")
        print()

    print_sync_dates()

    if not all_ok:
        print("\nOne or more expected tables are empty. Has the ETL run completed successfully?", file=sys.stderr)
        return 1

    print("\nDemo verification passed: all tables populated for all sellers.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
