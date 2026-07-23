from pathlib import Path

import aiosqlite

from my_marketplace_etl.config import app_settings
from my_marketplace_etl.dto.source_records import ProductsRecord


class SqliteProductDbReader:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or Path(app_settings.SOURCE_SQLITE_PATH)

    async def fetch_products(self, seller_id: str, start: str, end: str) -> list[ProductsRecord]:
        conn = await aiosqlite.connect(self.db_path)
        try:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT * FROM source_products
                WHERE seller_id = ? AND date BETWEEN ? AND ?
                """,
                (seller_id, start, end),
            )
            rows = await cursor.fetchall()
            return [ProductsRecord.model_validate(dict(row)) for row in rows]
        finally:
            await conn.close()
