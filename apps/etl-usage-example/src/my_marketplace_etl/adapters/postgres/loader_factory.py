import asyncpg

from etl_core.common.logging.logger import LogSummaryEntry
from etl_core.modules.base.base_loader import BaseLoader
from etl_core.modules.base.relational_loader import RelationalLoader
from etl_core.ports.sync_state_store import SyncStateStore
from my_marketplace_etl.adapters.postgres.record_writer import PostgresRecordWriter
from my_marketplace_etl.config import app_settings
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import MarketplaceModelMixin
from my_marketplace_etl.ports.loader_factory import LoaderFactory


class PostgresLoaderFactory(LoaderFactory):
    def __init__(self, connection_pool: asyncpg.Pool):
        self.connection_pool = connection_pool
        self.record_writer = PostgresRecordWriter(connection_pool, app_settings)

    def create(
        self,
        seller: SellerEntity,
        model: type[MarketplaceModelMixin],
        sync_state_store: SyncStateStore,
        log_summary_entry: LogSummaryEntry,
    ) -> BaseLoader:
        return RelationalLoader(
            tenant_id=seller.id,
            model=model,
            sync_state_store=sync_state_store,
            record_writer=self.record_writer,
            log_summary_entry=log_summary_entry,
            is_debug=app_settings.IS_DEBUG,
        )
