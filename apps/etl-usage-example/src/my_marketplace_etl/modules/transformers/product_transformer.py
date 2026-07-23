import pandas as pd

from etl_core.common.logging.logger import LogSummaryEntry, log_execution, log_success
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.base_transformer import BaseTransformer
from my_marketplace_etl.common.data.cleaning import fill_null_int, parse_amount
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.models.marketplace_models import ProductModel


class ProductTransformer(BaseTransformer):
    def __init__(self, seller: SellerEntity):
        self.seller = seller
        self.log_summary_entry = LogSummaryEntry(entity_name="Product", action_type=LogActionTypeEnum.TRANSFORMATION)

    def __repr__(self):
        return "Product"

    def _consolidated_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        return pd.DataFrame(df["products"].iloc[0])

    @log_execution()
    def transform(self, df: pd.DataFrame, request_id: str) -> list[dict]:
        result = self._consolidated_df(df)
        if result.empty:
            return []
        result = result.rename(
            columns={
                "product_category_name": "category",
                "product_sub_category_name": "subcategory",
                "product_department_name": "department",
                "product_brand": "brand",
                "product_price": "sales_price",
                "product_stock_quantity": "stock",
                "product_stock_reserved_quantity": "reserved_stock",
                "product_stock_coverage_days": "stock_coverage_in_days",
            }
        )
        model_columns = set(ProductModel.column_names())
        records = []
        for row in result.to_dict(orient="records"):
            row["seller_id"] = row.get("seller_id") or self.seller.id
            row["sales_price"] = parse_amount(row.get("sales_price"))
            row["stock"] = fill_null_int(row.get("stock"), default=0)
            row["reserved_stock"] = fill_null_int(row.get("reserved_stock"), default=0)
            row["stock_coverage_in_days"] = fill_null_int(row.get("stock_coverage_in_days"), default=0)
            records.append({k: v for k, v in row.items() if k in model_columns})
        log_success("Product", LogActionTypeEnum.TRANSFORMATION, f"pid={request_id} transformed {len(records)} products")
        return records
