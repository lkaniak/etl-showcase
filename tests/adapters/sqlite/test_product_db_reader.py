import aiosqlite
import pytest

from my_marketplace_etl.adapters.sqlite.product_db_reader import SqliteProductDbReader

MIGRATION = """
CREATE TABLE IF NOT EXISTS source_products (
    seller_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_sku_id TEXT NOT NULL,
    date TEXT NOT NULL,
    product_category_name TEXT,
    product_sub_category_name TEXT,
    product_department_name TEXT,
    product_brand TEXT,
    product_price TEXT,
    product_sold_quantity TEXT,
    product_stock_quantity INTEGER,
    product_stock_reserved_quantity INTEGER,
    product_stock_coverage_days INTEGER,
    PRIMARY KEY (seller_id, product_id, product_sku_id, date)
);
"""

ROWS = [
    ("seller_a", "prod-1", "sku-1", "2024-06-01", "Electronics", "Phones", "Mobile", "Acme", "999.90", "10", 50, 5, 12),
    ("seller_a", "prod-2", "sku-2", "2024-06-01", "Home", "Kitchen", "Appliances", "Beta", "450,00", "3", 20, 2, None),
    ("seller_a", "prod-3", "sku-3", "2024-06-01", "Sports", None, None, "Gamma", "120.00", None, 15, 1, 8),
]

INSERT_SQL = """
INSERT INTO source_products (
    seller_id, product_id, product_sku_id, date,
    product_category_name, product_sub_category_name, product_department_name,
    product_brand, product_price, product_sold_quantity,
    product_stock_quantity, product_stock_reserved_quantity, product_stock_coverage_days
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


async def _seed_db(db_path):
    conn = await aiosqlite.connect(db_path)
    try:
        await conn.executescript(MIGRATION)
        await conn.executemany(INSERT_SQL, ROWS)
        await conn.commit()
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_sqlite_product_db_reader_fetches_rows_in_range(tmp_path):
    db_path = tmp_path / "marketplace_source.db"
    await _seed_db(db_path)
    reader = SqliteProductDbReader(db_path=db_path)

    products = await reader.fetch_products("seller_a", "2024-06-01", "2024-06-30")
    assert len(products) == 3
    assert products[0].product_id == "prod-1"


@pytest.mark.asyncio
async def test_sqlite_product_db_reader_returns_empty_for_out_of_range(tmp_path):
    db_path = tmp_path / "marketplace_source.db"
    await _seed_db(db_path)
    reader = SqliteProductDbReader(db_path=db_path)

    products = await reader.fetch_products("seller_a", "2023-01-01", "2023-01-31")
    assert products == []
