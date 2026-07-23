from abc import ABCMeta, abstractmethod
from datetime import datetime

import pandas as pd
from pydantic import BaseModel

from etl_core.common.data.string_handler import date_to_str, get_tenant_logger_header
from etl_core.common.logging.logger import log_error, log_execution_async, log_info, log_success
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum


class BaseExtractor(metaclass=ABCMeta):
    @abstractmethod
    async def extractor_func(
        self, initial_date: str, final_date: str, request_id: str
    ) -> list[BaseModel]:
        raise NotImplementedError

    @log_execution_async()
    async def extract(
        self, initial_date: datetime, final_date: datetime, request_id: str
    ) -> pd.DataFrame:
        log_params = {
            "entity_name": self.__repr__(),
            "action_type": LogActionTypeEnum.EXTRACTION,
        }
        try:
            log_params["message"] = (
                f"pid={request_id}---{get_tenant_logger_header(self)} Executing {self.__repr__()} "
                f"from {initial_date} to {final_date}"
            )
            log_info(**log_params)
            response = await self.extractor_func(
                initial_date=date_to_str(initial_date),
                final_date=date_to_str(final_date),
                request_id=request_id,
            )
            df = pd.DataFrame([instance.model_dump() for instance in response])
            log_params["message"] = (
                f"pid={request_id}---{get_tenant_logger_header(self)} Successfully executed "
                f"{self.__repr__()} Extractor and fetched {len(response)} rows"
            )
            log_success(**log_params)
            return df
        except Exception as e:
            log_params["message"] = (
                f"pid={request_id}---{get_tenant_logger_header(self)} Error extracting "
                f"{self.__repr__()} data: {e}"
            )
            log_error(**log_params)
            raise
