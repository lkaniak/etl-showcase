import asyncio
import uuid
from collections import defaultdict
from pathlib import Path

from loguru import logger

from etl_core.common.logging.logger import LogEntry, LogExecutionStatusEnum, print_log_execution_summary
from etl_core.entities.enum import SyncStatusType, SyncType
from etl_core.infra.concurrency.parallelism import engine_worker
from my_marketplace_etl.adapters.http.mock_source_api_client import MockSourceApiClient
from my_marketplace_etl.adapters.mongo.mongo_repositories import MongoConfigStore, MongoSyncStateStore
from my_marketplace_etl.adapters.mysql.product_db_reader import MysqlProductDbReader
from my_marketplace_etl.adapters.postgres.connection import get_postgresql_connection_pool
from my_marketplace_etl.adapters.postgres.loader_factory import PostgresLoaderFactory
from my_marketplace_etl.adapters.sqlite.connection import get_sqlite_connection_pool
from my_marketplace_etl.adapters.sqlite.loader_factory import SqliteLoaderFactory
from my_marketplace_etl.adapters.sqlite.product_db_reader import SqliteProductDbReader
from my_marketplace_etl.config import app_settings
from my_marketplace_etl.engine.marketplace_etl_engine import MarketplaceEtlEngine
from my_marketplace_etl.entities.seller_entities import EtlSettingsEntity
from my_marketplace_etl.ports.product_db_reader import ProductDbReader


def is_sync_available(seller_id: str, settings_by_seller: dict[str, EtlSettingsEntity]) -> bool:
    settings = settings_by_seller[seller_id]
    if settings.sync_status != SyncStatusType.AVAILABLE.value:
        return False
    sync_values = list(settings.sync_dates.model_dump().values())
    if app_settings.APP_SYNC_TYPE == SyncType.INCREMENTAL.value:
        return any(sync_values)
    if app_settings.APP_SYNC_TYPE == SyncType.FIRST.value:
        return any(value == "" for value in sync_values)
    return True


async def create_loader_factory(seller_relational_database_name: str):
    if app_settings.TARGET_DB_BACKEND == "sqlite":
        db_path = Path(app_settings.TARGET_DB_SQLITE_BASE_PATH) / f"{seller_relational_database_name}.db"
        pool = get_sqlite_connection_pool(db_path)
        return SqliteLoaderFactory(pool)
    pool = await get_postgresql_connection_pool(seller_relational_database_name, app_settings)
    return PostgresLoaderFactory(pool)


def create_product_source() -> ProductDbReader:
    backend = app_settings.SOURCE_PRODUCT_BACKEND
    if backend == "api":
        return MockSourceApiClient()
    if backend == "sqlite":
        return SqliteProductDbReader()
    if backend == "mysql":
        return MysqlProductDbReader()
    raise ValueError(f"Unsupported SOURCE_PRODUCT_BACKEND: {backend}")


async def main():
    logger.info("Starting marketplace ETL...")
    config_store = MongoConfigStore()
    sync_state_store = MongoSyncStateStore()
    order_source = MockSourceApiClient()
    traffic_source = MockSourceApiClient()
    product_source = create_product_source()

    sellers = config_store.get_eligible_sellers(
        app_settings.APP_SELLERS_TO_RUN, app_settings.APP_SELLERS_TO_IGNORE
    )
    settings_by_seller: dict[str, EtlSettingsEntity] = defaultdict(EtlSettingsEntity)
    for connector in sellers:
        settings_by_seller[connector.seller_id] = config_store.get_etl_settings(connector.seller_id)

    eligible = [s for s in sellers if is_sync_available(s.seller_id, settings_by_seller)]
    logger.info(f"Processing {len(eligible)} sellers")

    semaphore = asyncio.Semaphore(app_settings.MAX_RUNNER_EXECUTIONS)
    engines = []
    for connector in eligible:
        seller = config_store.get_seller(connector.seller_id)
        loader_factory = await create_loader_factory(seller.relational_database_name)
        engine_id = str(uuid.uuid4())
        engines.append(
            MarketplaceEtlEngine(
                seller=seller,
                sync_dates=settings_by_seller[seller.id].sync_dates.model_dump(),
                retention_period_data=connector.retention_period_data,
                loader_factory=loader_factory,
                sync_state_store=sync_state_store,
                order_source=order_source,
                traffic_source=traffic_source,
                product_source=product_source,
                uuid=engine_id,
                sync_type=SyncType(app_settings.APP_SYNC_TYPE),
            )
        )

    async def run_engine(engine: MarketplaceEtlEngine):
        async with semaphore:
            if not app_settings.IS_DEBUG:
                config_store.set_sync_status(engine.seller.id, SyncStatusType.PROCESSING.value)
            await engine_worker(f"({engine.seller.id}) {engine.seller.name}", engine, engine.uuid)
            config_store.set_sync_status(engine.seller.id, SyncStatusType.AVAILABLE.value)

    await asyncio.gather(*[run_engine(engine) for engine in engines], return_exceptions=True)
    print_log_execution_summary(limit=20)
    print_log_execution_summary(filter_entry=LogEntry(status=LogExecutionStatusEnum.ERROR))
    logger.info("Marketplace ETL finished.")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
