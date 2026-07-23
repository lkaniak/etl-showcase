from typing import Protocol

from my_marketplace_etl.dto.source_records import TrafficRecord


class TrafficSourceClient(Protocol):
    async def fetch_traffic(self, seller_id: str, start: str, end: str) -> list[TrafficRecord]: ...
