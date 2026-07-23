from datetime import datetime

from etl_core.common.data.string_handler import date_to_str
from etl_core.common.logging.logger import LogSummaryEntry, log_execution_async
from etl_core.modules.base.base_loader import BaseLoader
from etl_core.ports.base_etl_model import BaseEtlModel
from etl_core.ports.record_writer import RecordWriter
from etl_core.ports.sync_state_store import SyncStateStore


class RelationalLoader(BaseLoader):
    def __init__(
        self,
        tenant_id: str,
        model: type[BaseEtlModel],
        sync_state_store: SyncStateStore,
        record_writer: RecordWriter,
        log_summary_entry: LogSummaryEntry,
        is_debug: bool = False,
    ):
        self.tenant_id = tenant_id
        self.model = model
        self.sync_date_property = model.__syncdateentity__
        self.sync_state_store = sync_state_store
        self.record_writer = record_writer
        self.last_sync_date = ""
        self.log_summary_entry = log_summary_entry
        self.is_debug = is_debug

    @log_execution_async()
    async def load(self, data: list[dict], current_sync_date: datetime) -> int:
        exception = None
        amount = 0
        try:
            deduped = BaseLoader.dedup(data, self.model)
            await self.record_writer.upsert_records(self.model, deduped)
            self.last_sync_date = date_to_str(current_sync_date)
            amount = len(deduped)
        except Exception as e:
            exception = e
        finally:
            if not self.is_debug:
                self.sync_state_store.update_sync_dates(
                    self.tenant_id,
                    {self.sync_date_property: self.last_sync_date},
                )
            if exception:
                raise exception
        return amount

    async def mark_sync_date(self, current_sync_date: datetime) -> None:
        if self.is_debug:
            return
        self.sync_state_store.update_sync_dates(
            self.tenant_id,
            {self.sync_date_property: date_to_str(current_sync_date)},
        )
