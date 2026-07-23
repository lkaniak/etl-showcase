from datetime import datetime

from etl_core.common.data.date_handler import DATE_OPERATORS, translate_date_period_param
from my_marketplace_etl.adapters.postgres.custom_update.entities import (
    IgnoreColumnsToUpdateOnUpsertMetadata,
    IgnoreColumnsToUpdateOnUpsertParams,
)
from my_marketplace_etl.adapters.postgres.upsert_query import build_upsert_query


class IgnoreColumnsToUpdateOnUpsert:
    def __repr__(self):
        return "ignore_columns_to_update_on_upsert"

    @classmethod
    def impl(
        cls,
        rows: list[dict],
        config: IgnoreColumnsToUpdateOnUpsertParams,
        metadata: IgnoreColumnsToUpdateOnUpsertMetadata,
    ):
        date_operator_config = config.date_operator
        date_operator_periods = date_operator_config.period
        date_operator = date_operator_config.operator
        columns_to_ignore = config.columns
        lower_bound = (
            None
            if not date_operator_periods.lower_bound
            else datetime.fromisoformat(translate_date_period_param(date_operator_periods.lower_bound))
        )
        upper_bound = (
            None
            if not date_operator_periods.upper_bound
            else datetime.fromisoformat(translate_date_period_param(date_operator_periods.upper_bound))
        )

        rows_with_hash = {metadata.get_row_hash(row): row for row in rows}
        rows_to_operate = [
            row
            for row in rows
            if DATE_OPERATORS[date_operator](
                datetime.fromisoformat(row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])[:10]),
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
        ]
        for row in rows_to_operate:
            del rows_with_hash[metadata.get_row_hash(row)]
        remaining_rows = list(rows_with_hash.values())

        query, params = build_upsert_query(
            table_name=metadata.table_name,
            rows=rows_to_operate,
            conflict_columns=metadata.primary_keys,
            update_columns=[column for column in metadata.data_columns if column not in columns_to_ignore],
        )
        return query, params, remaining_rows
