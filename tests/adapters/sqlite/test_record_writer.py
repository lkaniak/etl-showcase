import pytest

from my_marketplace_etl.adapters.sqlite.connection import get_sqlite_connection_pool
from my_marketplace_etl.adapters.sqlite.record_writer import SqliteRecordWriter
from my_marketplace_etl.config import Settings
from my_marketplace_etl.models.marketplace_models import OrderModel


@pytest.mark.asyncio
async def test_sqlite_record_writer_upserts_records(tmp_path):
    db_path = tmp_path / "seller_a.db"
    pool = get_sqlite_connection_pool(db_path)
    config = Settings()
    writer = SqliteRecordWriter(pool, config)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT NOT NULL,
                    seller_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    shipping_state TEXT,
                    shipping_city TEXT,
                    coupon_code TEXT,
                    PRIMARY KEY (order_id, seller_id, date)
                )
                """,
                (),
            )

    records = [
        {
            "order_id": "ord-1",
            "seller_id": "seller_a",
            "date": "2024-06-01",
            "status": "PAID",
            "total_amount": 100.0,
            "shipping_state": None,
            "shipping_city": None,
            "coupon_code": None,
        }
    ]
    await writer.upsert_records(OrderModel, records)

    async with pool.acquire() as conn:
        cursor = await conn._conn.execute(
            "SELECT status FROM orders WHERE order_id = ? AND seller_id = ? AND date = ?",
            ("ord-1", "seller_a", "2024-06-01"),
        )
        row = await cursor.fetchone()
        assert row[0] == "PAID"

    records[0]["status"] = "SHIPPED"
    await writer.upsert_records(OrderModel, records)

    async with pool.acquire() as conn:
        cursor = await conn._conn.execute(
            "SELECT status FROM orders WHERE order_id = ? AND seller_id = ? AND date = ?",
            ("ord-1", "seller_a", "2024-06-01"),
        )
        row = await cursor.fetchone()
        assert row[0] == "SHIPPED"
