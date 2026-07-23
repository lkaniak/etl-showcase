from typing import Protocol

from my_marketplace_etl.dto.source_records import ProductsRecord


class ProductDbReader(Protocol):
    async def fetch_products(self, seller_id: str, start: str, end: str) -> list[ProductsRecord]: ...
