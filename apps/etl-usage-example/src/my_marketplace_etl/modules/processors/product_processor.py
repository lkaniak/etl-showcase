from datetime import datetime

from etl_core.common.data.date_handler import (
    calculate_timeout_based_on_periods,
    get_next_day,
    get_next_initial_final_dates,
    get_next_x_days,
)
from etl_core.common.data.string_handler import DATE_FORMAT
from etl_core.common.logging.logger import LogSummaryEntry, log_execution_async
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.entities.etl_processor_entity import EtlProcessorEntity
from etl_core.modules.base.base_processor import BaseProcessor
from etl_core.ports.sync_state_store import SyncStateStore
from my_marketplace_etl.config import app_settings
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import ProductModel
from my_marketplace_etl.modules.extractors.product_extractor import ProductExtractor
from my_marketplace_etl.modules.transformers.product_transformer import ProductTransformer
from my_marketplace_etl.ports.loader_factory import LoaderFactory
from my_marketplace_etl.ports.product_db_reader import ProductDbReader


class ProductProcessor(BaseProcessor):
    def __init__(
        self,
        last_sync_date: str,
        seller: SellerEntity,
        source: ProductDbReader,
        stop_date: datetime,
        loader_factory: LoaderFactory,
        sync_state_store: SyncStateStore,
    ):
        self.log_summary_entry = LogSummaryEntry(entity_name="Product", action_type=LogActionTypeEnum.PROCESSOR)
        self.seller = seller
        self.stop_date = stop_date
        self.initial_date, self.final_date = get_next_initial_final_dates(
            stop_date=stop_date,
            final_date_func=get_next_x_days,
            initial_date_func=datetime.strptime,
            initial_date_func_args=[last_sync_date, DATE_FORMAT],
            final_date_func_args=[30],
        )
        self.timeout = calculate_timeout_based_on_periods(
            self.initial_date, self.stop_date, period=30, min_timeout=60 * 60
        )
        self.extractor = ProductExtractor(source=source, seller=seller)
        self.transformer_product = ProductTransformer(seller=seller)
        self.loader_product = loader_factory.create(
            seller, ProductModel, sync_state_store, LogSummaryEntry(entity_name="Product", action_type=LogActionTypeEnum.LOADER)
        )

    def __repr__(self):
        return "Product"

    def get_next_days(self):
        return get_next_initial_final_dates(
            stop_date=self.stop_date,
            final_date_func=get_next_x_days,
            initial_date_func=get_next_day,
            initial_date_func_args=[self.final_date],
            final_date_func_args=[30],
        )

    @log_execution_async()
    async def execute(self) -> None:
        entity_configs = [
            EtlProcessorEntity(
                name="Product", transformer=self.transformer_product, loader=self.loader_product, payload=[]
            ),
        ]
        await self._execute_multiple(entity_configs, app_settings)
