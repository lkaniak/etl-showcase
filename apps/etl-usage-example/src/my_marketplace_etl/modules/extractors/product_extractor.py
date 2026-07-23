from datetime import datetime

import pandas as pd

from etl_core.common.data.string_handler import date_to_str, get_tenant_logger_header
from etl_core.common.logging.logger import LogSummaryEntry, log_error, log_execution_async, log_info, log_success
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.base_extractor import BaseExtractor
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.ports.product_db_reader import ProductDbReader


class ProductExtractor(BaseExtractor):
    def __init__(self, source: ProductDbReader, seller: SellerEntity):
        self.source = source
        self.seller = seller
        self.log_summary_entry = LogSummaryEntry(entity_name="Product", action_type=LogActionTypeEnum.EXTRACTION)

    def __repr__(self):
        return "Product"

    async def extractor_func(self, initial_date: str, final_date: str, request_id: str):
        raise NotImplementedError

    @log_execution_async()
    async def extract(self, initial_date: datetime, final_date: datetime, request_id: str) -> pd.DataFrame:
        try:
            log_info(
                "Product",
                LogActionTypeEnum.EXTRACTION,
                f"pid={request_id}---{get_tenant_logger_header(self)} Executing Product from {initial_date} to {final_date}",
            )
            start = date_to_str(initial_date)
            end = date_to_str(final_date)
            products = await self.source.fetch_products(self.seller.id, start, end)
            data = [{"products": [item.model_dump() for item in products]}]
            log_success(
                "Product",
                LogActionTypeEnum.EXTRACTION,
                f"pid={request_id}---{get_tenant_logger_header(self)} fetched product source rows",
            )
            return pd.DataFrame(data)
        except Exception as e:
            log_error(
                "Product",
                LogActionTypeEnum.EXTRACTION,
                f"pid={request_id}---{get_tenant_logger_header(self)} Error extracting product data: {e}",
            )
            raise
