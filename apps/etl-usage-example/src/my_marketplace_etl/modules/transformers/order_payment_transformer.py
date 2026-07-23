import pandas as pd

from etl_core.common.logging.logger import LogSummaryEntry, log_execution, log_success
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.base_loader import BaseLoader
from etl_core.modules.base.base_transformer import BaseTransformer
from my_marketplace_etl.common.data.cleaning import parse_amount
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import OrderPaymentModel


class OrderPaymentTransformer(BaseTransformer):
    def __init__(self, seller: SellerEntity):
        self.seller = seller
        self.log_summary_entry = LogSummaryEntry(
            entity_name="OrderPayment", action_type=LogActionTypeEnum.TRANSFORMATION
        )

    def __repr__(self):
        return "OrderPayment"

    @log_execution()
    def transform(self, df: pd.DataFrame, request_id: str) -> list[dict]:
        if df.empty or "payments" not in df.columns:
            return []
        payments = []
        for row in df.itertuples(index=False):
            row_dict = row._asdict()
            for item in row_dict.get("payments") or []:
                if isinstance(item, dict):
                    item = {**item}
                    item.setdefault("seller_id", self.seller.id)
                    if "paymentMethod" in item and "method" not in item:
                        item["method"] = item.pop("paymentMethod")
                    item["amount"] = parse_amount(item.get("amount"))
                    payments.append(item)
        deduped = BaseLoader.dedup(payments, OrderPaymentModel)
        model_columns = set(OrderPaymentModel.column_names())
        records = [{k: v for k, v in row.items() if k in model_columns} for row in deduped if row.get("payment_id")]
        log_success(
            "OrderPayment",
            LogActionTypeEnum.TRANSFORMATION,
            f"pid={request_id} transformed {len(records)} order payments",
        )
        return records
