from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from my_marketplace_etl.adapters.http.mock_source_api_client import MockSourceApiClient


@pytest.mark.asyncio
async def test_mock_source_api_client_fetch_products():
    response = MagicMock()
    response.json.return_value = [
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
        }
    ]
    response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("my_marketplace_etl.adapters.http.mock_source_api_client.httpx.AsyncClient", return_value=mock_client):
        client = MockSourceApiClient(base_url="http://testserver")
        products = await client.fetch_products("seller_a", "2024-06-01", "2024-06-30")

    assert len(products) == 1
    assert products[0].product_id == "prod-1"
    mock_client.get.assert_awaited_once_with(
        "/sellers/seller_a/products",
        params={"from": "2024-06-01", "to": "2024-06-30"},
    )
