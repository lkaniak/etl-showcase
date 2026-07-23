import pandas as pd
import pytest

from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.modules.transformers.order_payment_transformer import OrderPaymentTransformer
from my_marketplace_etl.modules.transformers.order_transformer import OrderTransformer
from my_marketplace_etl.modules.transformers.product_transformer import ProductTransformer
from my_marketplace_etl.modules.transformers.traffic_transformer import TrafficTransformer


@pytest.fixture
def seller():
    return SellerEntity(id="seller_a", name="Seller Alpha", relational_database_name="seller_a_db")


def test_order_transformer_cleans_dirty_amounts_and_status(seller):
    df = pd.DataFrame(
        [
            {
                "order_id": "ord-1001",
                "seller_id": "seller_a",
                "date": "2024-06-01",
                "status": "PAID",
                "total_amount": "1,234.50",
                "customer_state": "SP",
                "customer_city": "Sao Paulo",
                "coupon_name": "",
                "legacy_field": "ignore-me",
            }
        ]
    )
    result = OrderTransformer(seller).transform(df, "req-1")
    assert len(result) == 1
    row = result[0]
    assert row["status"] == "paid"
    assert row["total_amount"] == 1234.50
    assert row["shipping_state"] == "SP"
    assert row["coupon_code"] is None
    assert "legacy_field" not in row


def test_order_transformer_skips_invalid_rows(seller):
    df = pd.DataFrame(
        [
            {"order_id": "", "total_amount": "10", "date": "2024-06-01", "status": "paid"},
            {"order_id": "ord-x", "total_amount": "-5", "date": "2024-06-01", "status": "paid"},
        ]
    )
    assert OrderTransformer(seller).transform(df, "req-1") == []


def test_order_payment_transformer_flattens_nested_payments(seller):
    df = pd.DataFrame(
        [
            {
                "order_id": "ord-1001",
                "payments": [
                    {"order_id": "ord-1001", "payment_id": "pay-1", "paymentMethod": "credit_card", "amount": "1234.50", "paid_at": "2024-06-01"},
                    {"order_id": "ord-1001", "payment_id": "pay-1", "method": "credit_card", "amount": "1234.50", "paid_at": "2024-06-01"},
                ],
            }
        ]
    )
    result = OrderPaymentTransformer(seller).transform(df, "req-1")
    assert len(result) == 1
    assert result[0]["method"] == "credit_card"
    assert result[0]["amount"] == 1234.50
    assert result[0]["seller_id"] == "seller_a"


def test_traffic_transformer_normalizes_source_and_fills_nulls(seller):
    df = pd.DataFrame(
        [
            {
                "seller_id": "seller_a",
                "date": "2024-06-01",
                "source": "Google / CPC",
                "medium": "cpc",
                "sessions": None,
                "users": 80,
                "pageviews": 320,
            }
        ]
    )
    result = TrafficTransformer(seller).transform(df, "req-1")
    assert len(result) == 1
    assert result[0]["source"] == "google / cpc"
    assert result[0]["sessions"] == 0
    assert result[0]["users"] == 80


def test_product_transformer_maps_catalog_fields(seller):
    df = pd.DataFrame(
        [
            {
                "products": [
                    {
                        "seller_id": "seller_a",
                        "product_id": "prod-1",
                        "product_sku_id": "sku-1",
                        "date": "2024-06-01",
                        "product_category_name": "Electronics",
                        "product_brand": "Acme",
                        "product_price": "999.90",
                    },
                    {
                        "seller_id": "seller_a",
                        "product_id": "prod-3",
                        "product_sku_id": "sku-3",
                        "date": "2024-06-01",
                        "product_category_name": "Sports",
                        "product_brand": "Gamma",
                        "product_price": "120.00",
                    },
                ],
            }
        ]
    )
    result = ProductTransformer(seller).transform(df, "req-1")
    assert len(result) == 2
    by_id = {row["product_id"]: row for row in result}
    assert by_id["prod-1"]["category"] == "Electronics"
    assert by_id["prod-1"]["sales_price"] == 999.90
    assert by_id["prod-3"]["brand"] == "Gamma"


def test_product_transformer_includes_stock_fields(seller):
    df = pd.DataFrame(
        [
            {
                "products": [
                    {
                        "seller_id": "seller_a",
                        "product_id": "prod-1",
                        "product_sku_id": "sku-1",
                        "date": "2024-06-01",
                        "product_stock_quantity": 50,
                        "product_stock_reserved_quantity": 5,
                        "product_stock_coverage_days": None,
                    }
                ],
            }
        ]
    )
    result = ProductTransformer(seller).transform(df, "req-1")
    assert len(result) == 1
    row = result[0]
    assert row["stock"] == 50
    assert row["reserved_stock"] == 5
    assert row["stock_coverage_in_days"] == 0
