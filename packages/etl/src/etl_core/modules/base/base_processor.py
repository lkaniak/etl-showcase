import uuid
from datetime import datetime
from textwrap import dedent
from typing import Tuple

import pandas as pd
from pydantic_settings import BaseSettings

from etl_core.common.data.date_handler import (
    get_first_day_from_next_month,
    get_last_day_of_the_month,
    get_next_initial_final_dates,
)
from etl_core.common.data.string_handler import get_tenant_logger_header
from etl_core.common.logging.logger import log_error, log_execution_async, log_info, log_success
from etl_core.config import core_settings
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.entities.etl_processor_entity import EtlProcessorEntity
from etl_core.entities.exceptions.multiple_exception import MultipleExceptions
from etl_core.modules.base.base_loader import BaseLoader
from etl_core.modules.base.base_transformer import BaseTransformer


class BaseProcessor:
    async def _execute_multiple(self, entities: list[EtlProcessorEntity], app_settings: BaseSettings):
        exceptions = []
        last_day_processed = self.final_date
        while self.initial_date <= self.stop_date:
            req_id = str(uuid.uuid4())
            try:
                data = await self.extractor.extract(
                    self.initial_date, self.final_date, request_id=req_id
                )
            except Exception:
                break
            last_day_processed = self.final_date
            self.initial_date, self.final_date = self.get_next_days()
            for entity_config in entities:
                try:
                    result = await self.load_transform(
                        entity_config.name,
                        entity_config.transformer,
                        entity_config.loader,
                        data,
                        entity_config.payload,
                        last_day_processed,
                        req_id,
                    )
                    if result is not None:
                        entity_config.payload = result
                except Exception as e:
                    exceptions.append(e)
                    break

        for entity_config in entities:
            payload = entity_config.payload
            while payload:
                row_size = len(payload[0].keys())
                max_rows = app_settings.DB_QUERY_BIND_PARAMETERS_LIMIT // row_size
                chunk = payload[: min(max_rows, len(payload))]
                try:
                    await self.load_data_payload(
                        entity_name=entity_config.name,
                        loader=entity_config.loader,
                        data_payload=chunk,
                        last_day_processed=last_day_processed,
                        remaining=len(payload) - len(chunk),
                        request_id=req_id,
                    )
                except Exception as e:
                    exceptions.append(e)
                payload = payload[max_rows:]

        if exceptions:
            raise MultipleExceptions.handle_multiple_exceptions(exceptions=exceptions)

    def get_next_days(self) -> Tuple[datetime, datetime]:
        return get_next_initial_final_dates(
            stop_date=self.stop_date,
            final_date_func=get_last_day_of_the_month,
            initial_date_func=get_first_day_from_next_month,
            initial_date_func_args=[self.initial_date],
        )

    @log_execution_async()
    async def execute(self) -> None:
        data_payload = []
        exceptions = []
        last_day_processed = self.final_date
        while self.initial_date <= self.stop_date:
            req_id = str(uuid.uuid4())
            try:
                data = await self.extractor.extract(self.initial_date, self.final_date, req_id)
            except Exception as e:
                exceptions.append(e)
                break
            last_day_processed = self.final_date
            try:
                load_transform_result = await self.load_transform(
                    entity_name=self.__repr__(),
                    transformer=self.transformer,
                    loader=self.loader,
                    data=data,
                    data_payload=data_payload,
                    last_day_processed=last_day_processed,
                    request_id=req_id,
                )
            except Exception as e:
                exceptions.append(e)
                break
            if load_transform_result is not None:
                data_payload = load_transform_result
            self.initial_date, self.final_date = self.get_next_days()

        while data_payload:
            row_size = len(data_payload[0].keys())
            max_rows = core_settings.DB_QUERY_BIND_PARAMETERS_LIMIT // row_size
            chunk = data_payload[: min(max_rows, len(data_payload))]
            data_payload = data_payload[max_rows:]
            try:
                await self.load_data_payload(
                    entity_name=self.__repr__(),
                    loader=self.loader,
                    data_payload=chunk,
                    last_day_processed=last_day_processed,
                    remaining=len(data_payload),
                    request_id=req_id,
                )
            except Exception as e:
                exceptions.append(e)

        if exceptions:
            raise MultipleExceptions.handle_multiple_exceptions(exceptions=exceptions)

    async def load_data_payload(
        self,
        entity_name: str,
        loader: BaseLoader,
        data_payload: list,
        last_day_processed: datetime,
        remaining: int,
        request_id: str,
    ):
        try:
            amount_loaded = await loader.load(data_payload, last_day_processed)
            log_success(
                entity_name=entity_name,
                action_type=LogActionTypeEnum.LOADER,
                message=dedent(
                    f"""pid={request_id}---{get_tenant_logger_header(self)} Loaded {entity_name}
                    with {amount_loaded} records. Remaining: {remaining}"""
                ),
            )
        except Exception as e:
            log_error(
                entity_name=entity_name,
                action_type=LogActionTypeEnum.LOADER,
                message=f"pid={request_id}---{get_tenant_logger_header(self)} Error loading {entity_name}: {e}",
            )
            raise

    async def load_transform(
        self,
        entity_name: str,
        transformer: BaseTransformer,
        loader: BaseLoader,
        data: pd.DataFrame,
        data_payload: list,
        last_day_processed,
        request_id: str,
    ) -> list[dict] | None:
        process_payload = data_payload.copy()
        if data.empty:
            log_info(
                entity_name,
                LogActionTypeEnum.EXTRACTION,
                f"pid={request_id}---{get_tenant_logger_header(self)} No {entity_name} data, skipping",
            )
            return process_payload
        transformed_data = transformer.transform(data, request_id)
        if not transformed_data:
            log_info(
                entity_name,
                LogActionTypeEnum.TRANSFORMATION,
                f"pid={request_id}---{get_tenant_logger_header(self)} no valid {entity_name} data, skipping",
            )
            await loader.mark_sync_date(last_day_processed)
            return []

        row_size = len(transformed_data[0].keys())
        max_rows = core_settings.DB_QUERY_BIND_PARAMETERS_LIMIT // row_size

        while transformed_data:
            capacity = max_rows - len(process_payload)
            if capacity <= 0:
                flush_chunk = process_payload[:max_rows]
                process_payload = process_payload[max_rows:]
                await self.load_data_payload(
                    entity_name,
                    loader,
                    flush_chunk,
                    last_day_processed,
                    len(transformed_data),
                    request_id,
                )
                continue
            take = min(capacity, len(transformed_data))
            process_payload.extend(transformed_data[:take])
            transformed_data = transformed_data[take:]

        return process_payload
