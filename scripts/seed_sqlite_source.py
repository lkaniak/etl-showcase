#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path

import aiosqlite

MIGRATION = (Path(__file__).resolve().parents[1] / "migrations/sqlite_source/001_init.sql").read_text()

ROWS = [
    ("seller_a", "prod-1", "sku-1", "2024-06-01", "Electronics", "Phones", "Mobile", "Acme", "999.90", "10", 50, 5, 12),
    ("seller_a", "prod-2", "sku-2", "2024-06-01", "Home", "Kitchen", "Appliances", "Beta", "450,00", "3", 20, 2, None),
    ("seller_a", "prod-3", "sku-3", "2024-06-01", "Sports", None, None, "Gamma", "120.00", None, 15, 1, 8),
    ("seller_b", "prod-9", "sku-9", "2024-06-10", "Fashion", "Shoes", "Footwear", "Delta", "199.00", "5", 30, 3, 10),
    ("seller_a", "prod-1", "sku-1", "2024-07-05", "Electronics", "Phones", "Mobile", "Acme", "979.90", "14", 42, 4, 9),
    ("seller_a", "prod-4", "sku-4", "2024-07-20", "Home", "Kitchen", "Appliances", "Beta", "210,00", "6", 12, 1, 7),
    ("seller_b", "prod-9", "sku-9", "2024-07-12", "Fashion", "Shoes", "Footwear", "Delta", "189.00", "8", 22, 2, 6),
]

INSERT_SQL = """
INSERT OR REPLACE INTO source_products (
    seller_id, product_id, product_sku_id, date,
    product_category_name, product_sub_category_name, product_department_name,
    product_brand, product_price, product_sold_quantity,
    product_stock_quantity, product_stock_reserved_quantity, product_stock_coverage_days
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


async def main():
    db_path = Path(os.getenv("SOURCE_SQLITE_PATH", "./data/sqlite_source/marketplace_source.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    try:
        await conn.executescript(MIGRATION)
        await conn.executemany(INSERT_SQL, ROWS)
        await conn.commit()
        print(f"Seeded SQLite source at {db_path}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
