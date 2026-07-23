import asyncpg
from pydantic_settings import BaseSettings


async def get_postgresql_connection_pool(database_name: str, config: BaseSettings) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=config.TARGET_DB_HOST,
        port=config.TARGET_DB_PORT,
        user=config.TARGET_DB_USER,
        password=config.TARGET_DB_PASSWORD,
        database=database_name,
        min_size=1,
        max_size=config.MAX_DB_POOL_SIZE,
    )
