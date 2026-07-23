from abc import ABCMeta, abstractmethod

import pandas as pd


class BaseTransformer(metaclass=ABCMeta):
    @abstractmethod
    def transform(self, df: pd.DataFrame, request_id: str) -> list[dict]:
        pass
