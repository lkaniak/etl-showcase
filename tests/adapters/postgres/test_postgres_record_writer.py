from datetime import date

from my_marketplace_etl.adapters.postgres.record_writer import _coerce_records_for_postgres
from my_marketplace_etl.models.marketplace_models import OrderModel, TrafficModel


def test_coerce_records_converts_date_strings_for_postgres():
    records = [
        {
            "seller_id": "seller_a",
            "date": "2024-06-01",
            "source": "google",
            "medium": "cpc",
            "sessions": 1,
            "users": 1,
            "pageviews": 1,
        }
    ]
    coerced = _coerce_records_for_postgres(TrafficModel, records)
    assert coerced[0]["date"] == date(2024, 6, 1)
    assert isinstance(coerced[0]["date"], date)


def test_coerce_records_leaves_non_date_columns_unchanged():
    records = [
        {
            "order_id": "ord-1",
            "seller_id": "seller_a",
            "date": "2024-06-01",
            "status": "paid",
            "total_amount": 100.0,
            "shipping_state": None,
            "shipping_city": None,
            "coupon_code": None,
        }
    ]
    coerced = _coerce_records_for_postgres(OrderModel, records)
    assert coerced[0]["status"] == "paid"
    assert coerced[0]["date"] == date(2024, 6, 1)
