from datetime import datetime

import pandas as pd

from etl_core.common.logging.logger import LogSummaryEntry, log_error, log_execution, log_success
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.base_transformer import BaseTransformer
from my_marketplace_etl.common.data.cleaning import empty_to_null, normalize_status, parse_amount
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import OrderModel


class OrderTransformer(BaseTransformer):
    def __init__(self, seller: SellerEntity):
        self.seller = seller
        self.log_summary_entry = LogSummaryEntry(entity_name="Order", action_type=LogActionTypeEnum.TRANSFORMATION)

    def __repr__(self):
        return "Order"

    @log_execution()
    def transform(self, df: pd.DataFrame, request_id: str) -> list[dict]:
        if df.empty:
            return []
        result = df.sort_values(by=["date"]).copy()
        result = result.rename(
            columns={"customer_state": "shipping_state", "customer_city": "shipping_city", "coupon_name": "coupon_code"}
        )
        records = []
        model_columns = set(OrderModel.column_names())
        skipped = 0
        for row in result.to_dict(orient="records"):
            if not row.get("order_id"):
                skipped += 1
                continue
            row["seller_id"] = row.get("seller_id") or self.seller.id
            row["status"] = normalize_status(row.get("status"))
            row["total_amount"] = parse_amount(row.get("total_amount"))
            row["shipping_state"] = empty_to_null(row.get("shipping_state"))
            row["shipping_city"] = empty_to_null(row.get("shipping_city"))
            row["coupon_code"] = empty_to_null(row.get("coupon_code"))
            filtered = {k: v for k, v in row.items() if k in model_columns}
            if filtered.get("total_amount") is None or filtered.get("total_amount", 0) < 0:
                skipped += 1
                continue
            records.append(filtered)
        log_success("Order", LogActionTypeEnum.TRANSFORMATION, f"pid={request_id} transformed {len(records)} orders, skipped {skipped}")
        return records
