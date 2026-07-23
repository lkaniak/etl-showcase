import pandas as pd

from etl_core.common.logging.logger import LogSummaryEntry, log_execution, log_success
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.base_transformer import BaseTransformer
from my_marketplace_etl.common.data.cleaning import fill_null_int, normalize_source_medium
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import TrafficModel


class TrafficTransformer(BaseTransformer):
    def __init__(self, seller: SellerEntity):
        self.seller = seller
        self.log_summary_entry = LogSummaryEntry(entity_name="Traffic", action_type=LogActionTypeEnum.TRANSFORMATION)

    def __repr__(self):
        return "Traffic"

    @log_execution()
    def transform(self, df: pd.DataFrame, request_id: str) -> list[dict]:
        if df.empty:
            return []
        records = []
        model_columns = set(TrafficModel.column_names())
        for row in df.to_dict(orient="records"):
            if not row.get("date"):
                continue
            row["seller_id"] = row.get("seller_id") or self.seller.id
            row["source"] = normalize_source_medium(row.get("source"))
            row["medium"] = normalize_source_medium(row.get("medium"))
            row["sessions"] = fill_null_int(row.get("sessions"))
            row["users"] = fill_null_int(row.get("users"))
            row["pageviews"] = fill_null_int(row.get("pageviews"))
            records.append({k: v for k, v in row.items() if k in model_columns})
        log_success("Traffic", LogActionTypeEnum.TRANSFORMATION, f"pid={request_id} transformed {len(records)} traffic rows")
        return records
