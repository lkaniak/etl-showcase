import aiomysql

from my_marketplace_etl.config import app_settings
from my_marketplace_etl.dto.source_records import ProductsRecord


class MysqlProductDbReader:
    async def _get_pool(self):
        return await aiomysql.create_pool(
            host=app_settings.SOURCE_MYSQL_HOST,
            port=app_settings.SOURCE_MYSQL_PORT,
            user=app_settings.SOURCE_MYSQL_USER,
            password=app_settings.SOURCE_MYSQL_PASSWORD,
            db=app_settings.SOURCE_MYSQL_DATABASE,
            autocommit=True,
        )

    async def fetch_products(self, seller_id: str, start: str, end: str) -> list[ProductsRecord]:
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT * FROM source_products
                        WHERE seller_id = %s AND date BETWEEN %s AND %s
                        """,
                        (seller_id, start, end),
                    )
                    rows = await cursor.fetchall()
            return [ProductsRecord.model_validate(row) for row in rows]
        finally:
            pool.close()
            await pool.wait_closed()
