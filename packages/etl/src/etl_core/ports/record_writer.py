from typing import Protocol

from etl_core.ports.base_etl_model import BaseEtlModel


class RecordWriter(Protocol):
    async def upsert_records(self, model: type[BaseEtlModel], records: list[dict]) -> None: ...
