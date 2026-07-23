import httpx

from my_marketplace_etl.config import app_settings
from my_marketplace_etl.dto.source_records import OrderRecord, ProductsRecord, TrafficRecord


class MockSourceApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or app_settings.MOCK_SOURCE_API_URL).rstrip("/")

    async def fetch_orders(self, seller_id: str, start: str, end: str) -> list[OrderRecord]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            response = await client.get(
                f"/sellers/{seller_id}/orders",
                params={"from": start, "to": end},
            )
            response.raise_for_status()
            return [OrderRecord.model_validate(item) for item in response.json()]

    async def fetch_traffic(self, seller_id: str, start: str, end: str) -> list[TrafficRecord]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            response = await client.get(
                f"/sellers/{seller_id}/traffic",
                params={"from": start, "to": end},
            )
            response.raise_for_status()
            return [TrafficRecord.model_validate(item) for item in response.json()]

    async def fetch_products(self, seller_id: str, start: str, end: str) -> list[ProductsRecord]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            response = await client.get(
                f"/sellers/{seller_id}/products",
                params={"from": start, "to": end},
            )
            response.raise_for_status()
            return [ProductsRecord.model_validate(item) for item in response.json()]
