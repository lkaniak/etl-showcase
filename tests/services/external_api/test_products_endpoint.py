import json

import pytest
from fastapi.testclient import TestClient

from mock_source_api.main import app


@pytest.fixture
def client(monkeypatch, tmp_path):
    seed_path = tmp_path / "seed_mock_api.json"
    seed_path.write_text(
        json.dumps(
            {
                "orders": {},
                "traffic": {},
                "products": {
                    "seller_a": [
                        {
                            "seller_id": "seller_a",
                            "product_id": "prod-1",
                            "product_sku_id": "sku-1",
                            "date": "2024-06-01",
                            "product_category_name": "Electronics",
                            "product_sub_category_name": "Phones",
                            "product_department_name": "Mobile",
                            "product_brand": "Acme",
                            "product_price": "999.90",
                            "product_sold_quantity": "10",
                            "product_stock_quantity": 50,
                            "product_stock_reserved_quantity": 5,
                            "product_stock_coverage_days": 12,
                        },
                        {
                            "seller_id": "seller_a",
                            "product_id": "prod-2",
                            "product_sku_id": "sku-2",
                            "date": "2024-07-05",
                            "product_category_name": "Home",
                            "product_sub_category_name": "Kitchen",
                            "product_department_name": "Appliances",
                            "product_brand": "Beta",
                            "product_price": "210,00",
                            "product_sold_quantity": "6",
                            "product_stock_quantity": 12,
                            "product_stock_reserved_quantity": 1,
                            "product_stock_coverage_days": 7,
                        },
                    ]
                },
            }
        )
    )
    data = json.loads(seed_path.read_text())
    monkeypatch.setattr("mock_source_api.main.SEED_PATH", seed_path)
    monkeypatch.setattr("mock_source_api.main.DATA", data)
    return TestClient(app)


def test_products_endpoint_filters_by_date_range(client):
    response = client.get("/sellers/seller_a/products", params={"from": "2024-06-01", "to": "2024-06-30"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["product_id"] == "prod-1"


def test_products_endpoint_returns_empty_for_unknown_seller(client):
    response = client.get("/sellers/seller_z/products", params={"from": "2024-06-01", "to": "2024-06-30"})
    assert response.status_code == 200
    assert response.json() == []
