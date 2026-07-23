from my_marketplace_etl.dto.source_records import OrderRecord
from my_marketplace_etl.ports.order_source import OrderSourceClient
from etl_core.common.logging.logger import LogSummaryEntry
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.base_extractor import BaseExtractor
from my_marketplace_etl.entities.seller_entities import SellerEntity


class OrderExtractor(BaseExtractor):
    def __init__(self, source: OrderSourceClient, seller: SellerEntity):
        self.source = source
        self.seller = seller
        self.log_summary_entry = LogSummaryEntry(entity_name="Order", action_type=LogActionTypeEnum.EXTRACTION)

    def __repr__(self):
        return "Order"

    async def extractor_func(self, initial_date: str, final_date: str, request_id: str) -> list[OrderRecord]:
        return await self.source.fetch_orders(self.seller.id, initial_date, final_date)
