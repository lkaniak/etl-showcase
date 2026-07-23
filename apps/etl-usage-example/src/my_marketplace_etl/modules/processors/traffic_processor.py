from datetime import datetime

from etl_core.common.data.date_handler import (
    calculate_timeout_based_on_periods,
    get_last_day_of_the_month,
    get_next_initial_final_dates,
)
from etl_core.common.data.string_handler import DATE_FORMAT
from etl_core.common.logging.logger import LogSummaryEntry
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.base_processor import BaseProcessor
from etl_core.ports.sync_state_store import SyncStateStore
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import TrafficModel
from my_marketplace_etl.modules.extractors.traffic_extractor import TrafficExtractor
from my_marketplace_etl.modules.transformers.traffic_transformer import TrafficTransformer
from my_marketplace_etl.ports.loader_factory import LoaderFactory
from my_marketplace_etl.ports.traffic_source import TrafficSourceClient


class TrafficProcessor(BaseProcessor):
    def __init__(
        self,
        last_sync_date: str,
        seller: SellerEntity,
        source: TrafficSourceClient,
        stop_date: datetime,
        loader_factory: LoaderFactory,
        sync_state_store: SyncStateStore,
    ):
        self.log_summary_entry = LogSummaryEntry(entity_name="Traffic", action_type=LogActionTypeEnum.PROCESSOR)
        self.seller = seller
        self.stop_date = stop_date
        self.initial_date, self.final_date = get_next_initial_final_dates(
            stop_date=stop_date,
            final_date_func=get_last_day_of_the_month,
            initial_date_func=datetime.strptime,
            initial_date_func_args=[last_sync_date, DATE_FORMAT],
        )
        self.timeout = calculate_timeout_based_on_periods(self.initial_date, self.stop_date, period=30)
        self.extractor = TrafficExtractor(source=source, seller=seller)
        self.transformer = TrafficTransformer(seller=seller)
        self.loader = loader_factory.create(
            seller, TrafficModel, sync_state_store, LogSummaryEntry(entity_name="Traffic", action_type=LogActionTypeEnum.LOADER)
        )

    def __repr__(self):
        return "Traffic"
