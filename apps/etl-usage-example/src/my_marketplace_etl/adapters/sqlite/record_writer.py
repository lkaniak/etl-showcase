import asyncio

from loguru import logger
from pydantic_settings import BaseSettings

from etl_core.ports.base_etl_model import BaseEtlModel
from my_marketplace_etl.adapters.postgres.custom_update.entities import (
    IgnoreColumnsToUpdateOnUpsertMetadata,
    IgnoreColumnsToUpdateOnUpsertParams,
)
from my_marketplace_etl.adapters.sqlite.connection import SqliteConnectionPool
from my_marketplace_etl.adapters.sqlite.custom_update.ignore_columns_to_update_on_upsert import (
    SqliteIgnoreColumnsToUpdateOnUpsert,
)
from my_marketplace_etl.adapters.sqlite.upsert_query import build_upsert_query


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise e
                    delay = min(base_delay * (2**attempt), max_delay)
                    logger.warning(f"Retry {attempt + 1} for {func.__name__} in {delay}s: {e}")
                    await asyncio.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


class SqliteRecordWriter:
    def __init__(self, connection_pool: SqliteConnectionPool, config: BaseSettings):
        self.connection_pool = connection_pool
        self.app_config = config
        self.custom_update_routines = {
            repr(SqliteIgnoreColumnsToUpdateOnUpsert()): SqliteIgnoreColumnsToUpdateOnUpsert.impl,
        }

    def _get_table_metadata(self, table: type[BaseEtlModel]) -> tuple[list[str], list[str]]:
        mapper = table.__mapper__
        primary_keys = [column.name for column in mapper.primary_key]
        primary_key_and_indexes = list(mapper.primary_key) + [
            col for index in table.__table__.indexes for col in index.columns
        ]
        data_columns = [
            column.name for column in mapper.columns if column not in primary_key_and_indexes
        ]
        return primary_keys, data_columns

    def _get_row_hash(self, row: dict, primary_keys: list[str]) -> str:
        return "_".join(str(row[col]) for col in primary_keys)

    def _get_custom_update_routines_query_params(
        self,
        table: type[BaseEtlModel],
        rows: list[dict],
        primary_keys: list[str],
        data_columns: list[str],
    ) -> tuple[list[dict], list[dict]]:
        custom_routines = []
        routines_dict = getattr(self.app_config, "APP_CUSTOM_UPDATE_ROUTINE", {}) or {}
        table_routines = routines_dict.get(table.__tablename__, {})
        for routine_name, routine_config in table_routines.items():
            handler = self.custom_update_routines.get(routine_name)
            if handler:
                query, params, rows = handler(
                    rows,
                    IgnoreColumnsToUpdateOnUpsertParams(**routine_config),
                    IgnoreColumnsToUpdateOnUpsertMetadata(
                        get_row_hash=lambda row: self._get_row_hash(row, primary_keys),
                        table_name=table.__tablename__,
                        primary_keys=primary_keys,
                        data_columns=data_columns,
                    ),
                )
                if query:
                    custom_routines.append({"query": query, "params": params})
        return rows, custom_routines

    @retry_with_backoff()
    async def upsert_rows(self, query_param_default: tuple[str, tuple], custom_updates: list[dict] | None = None):
        query_default, params_default = query_param_default
        custom_updates = custom_updates or []
        async with self.connection_pool.acquire() as conn:
            async with conn.transaction():
                for custom_update in custom_updates:
                    await conn.execute(custom_update["query"], custom_update["params"])
                if query_default:
                    await conn.execute(query_default, params_default)

    async def upsert_records(self, model: type[BaseEtlModel], records: list[dict]) -> None:
        if not records:
            return
        primary_keys, data_columns = self._get_table_metadata(model)
        updated_records, custom_updates = self._get_custom_update_routines_query_params(
            model, records, primary_keys, data_columns
        )
        query_param_default = build_upsert_query(
            table_name=model.__tablename__,
            rows=updated_records,
            conflict_columns=primary_keys,
            update_columns=data_columns,
        )
        await self.upsert_rows(query_param_default, custom_updates)
