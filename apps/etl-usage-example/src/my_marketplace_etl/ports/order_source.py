from typing import Protocol

from my_marketplace_etl.dto.source_records import OrderRecord


class OrderSourceClient(Protocol):
    async def fetch_orders(self, seller_id: str, start: str, end: str) -> list[OrderRecord]: ...
