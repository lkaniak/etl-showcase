from abc import ABCMeta, abstractmethod
from datetime import datetime

import pandas as pd

from etl_core.ports.base_etl_model import BaseEtlModel


class BaseLoader(metaclass=ABCMeta):
    sync_date_property: str
    is_debug: bool = False

    @abstractmethod
    async def load(self, data: list[dict], current_sync_date: datetime) -> int:
        pass

    @abstractmethod
    async def mark_sync_date(self, current_sync_date: datetime) -> None:
        pass

    @classmethod
    def dedup(cls, data: list[dict], table: type[BaseEtlModel]) -> list[dict]:
        df = pd.DataFrame(data)
        if not df.empty and df.duplicated(subset=table.__uniqueconstraints__).sum() > 0:
            df.drop_duplicates(
                subset=table.__uniqueconstraints__, ignore_index=False, keep="last", inplace=True
            )
        df = df.astype("object")
        df = df.where(df.notna(), None)
        return df.to_dict(orient="records")
