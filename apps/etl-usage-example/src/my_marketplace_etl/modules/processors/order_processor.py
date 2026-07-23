from datetime import datetime

from etl_core.common.data.date_handler import (
    calculate_timeout_based_on_periods,
    get_last_day_of_the_month,
    get_next_initial_final_dates,
)
from etl_core.common.data.string_handler import DATE_FORMAT
from etl_core.common.logging.logger import LogSummaryEntry, log_execution_async
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.entities.etl_processor_entity import EtlProcessorEntity
from etl_core.modules.base.base_processor import BaseProcessor
from etl_core.ports.sync_state_store import SyncStateStore
from my_marketplace_etl.config import app_settings
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import OrderModel, OrderPaymentModel
from my_marketplace_etl.modules.extractors.order_extractor import OrderExtractor
from my_marketplace_etl.modules.transformers.order_payment_transformer import OrderPaymentTransformer
from my_marketplace_etl.modules.transformers.order_transformer import OrderTransformer
from my_marketplace_etl.ports.loader_factory import LoaderFactory
from my_marketplace_etl.ports.order_source import OrderSourceClient


class OrderProcessor(BaseProcessor):
    def __init__(
        self,
        last_sync_date: str,
        seller: SellerEntity,
        source: OrderSourceClient,
        stop_date: datetime,
        loader_factory: LoaderFactory,
        sync_state_store: SyncStateStore,
    ):
        self.log_summary_entry = LogSummaryEntry(entity_name="Order", action_type=LogActionTypeEnum.PROCESSOR)
        self.seller = seller
        self.stop_date = stop_date
        self.initial_date, self.final_date = get_next_initial_final_dates(
            stop_date=stop_date,
            final_date_func=get_last_day_of_the_month,
            initial_date_func=datetime.strptime,
            initial_date_func_args=[last_sync_date, DATE_FORMAT],
        )
        self.timeout = calculate_timeout_based_on_periods(
            self.initial_date, self.stop_date, period=30, min_timeout=45 * 60
        )
        self.extractor = OrderExtractor(source=source, seller=seller)
        self.transformer_order = OrderTransformer(seller=seller)
        self.transformer_order_payment = OrderPaymentTransformer(seller=seller)
        self.loader_order = loader_factory.create(
            seller, OrderModel, sync_state_store, LogSummaryEntry(entity_name="Order", action_type=LogActionTypeEnum.LOADER)
        )
        self.loader_order_payment = loader_factory.create(
            seller,
            OrderPaymentModel,
            sync_state_store,
            LogSummaryEntry(entity_name="OrderPayment", action_type=LogActionTypeEnum.LOADER),
        )

    def __repr__(self):
        return "Order"

    @log_execution_async()
    async def execute(self) -> None:
        entity_configs = [
            EtlProcessorEntity(name="Order", transformer=self.transformer_order, loader=self.loader_order, payload=[]),
            EtlProcessorEntity(
                name="OrderPayment",
                transformer=self.transformer_order_payment,
                loader=self.loader_order_payment,
                payload=[],
            ),
        ]
        await self._execute_multiple(entity_configs, app_settings)
