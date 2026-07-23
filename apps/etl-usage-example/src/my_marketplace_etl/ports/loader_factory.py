from typing import Protocol

from etl_core.common.logging.logger import LogSummaryEntry
from etl_core.modules.base.base_loader import BaseLoader
from etl_core.ports.sync_state_store import SyncStateStore
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import MarketplaceModelMixin


class LoaderFactory(Protocol):
    def create(
        self,
        seller: SellerEntity,
        model: type[MarketplaceModelMixin],
        sync_state_store: SyncStateStore,
        log_summary_entry: LogSummaryEntry,
    ) -> BaseLoader: ...
