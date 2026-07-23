from datetime import datetime

import pytest

from etl_core.common.logging.logger import LogSummaryEntry
from etl_core.entities.enum.log_action_type_enum import LogActionTypeEnum
from etl_core.modules.base.relational_loader import RelationalLoader
from etl_core.ports.base_etl_model import BaseEtlModel


class FakeModel(BaseEtlModel):
    __tablename__ = "fake"
    __syncdateentity__ = "fake_entity"
    __uniqueconstraints__ = ["id"]

    def to_dict(self):
        return {}


class FakeRecordWriter:
    def __init__(self):
        self.records: list[tuple[type[BaseEtlModel], list[dict]]] = []

    async def upsert_records(self, model: type[BaseEtlModel], records: list[dict]) -> None:
        self.records.append((model, records))


class FakeSyncStateStore:
    def __init__(self):
        self.updates: list[tuple[str, dict[str, str]]] = []

    def update_sync_dates(self, tenant_id: str, payload: dict[str, str]) -> None:
        self.updates.append((tenant_id, payload))


@pytest.mark.asyncio
async def test_relational_loader_dedups_and_writes_records():
    writer = FakeRecordWriter()
    sync_state = FakeSyncStateStore()
    loader = RelationalLoader(
        tenant_id="seller_a",
        model=FakeModel,
        sync_state_store=sync_state,
        record_writer=writer,
        log_summary_entry=LogSummaryEntry(entity_name="Fake", action_type=LogActionTypeEnum.LOADER),
        is_debug=False,
    )
    data = [
        {"id": "1", "value": "a"},
        {"id": "1", "value": "b"},
    ]
    amount = await loader.load(data, datetime(2024, 6, 1))
    assert amount == 1
    assert len(writer.records) == 1
    assert writer.records[0][1] == [{"id": "1", "value": "b"}]
    assert sync_state.updates == [("seller_a", {"fake_entity": "2024-06-01"})]


@pytest.mark.asyncio
async def test_relational_loader_skips_sync_date_in_debug_mode():
    writer = FakeRecordWriter()
    sync_state = FakeSyncStateStore()
    loader = RelationalLoader(
        tenant_id="seller_a",
        model=FakeModel,
        sync_state_store=sync_state,
        record_writer=writer,
        log_summary_entry=LogSummaryEntry(entity_name="Fake", action_type=LogActionTypeEnum.LOADER),
        is_debug=True,
    )
    await loader.load([{"id": "1"}], datetime(2024, 6, 1))
    assert sync_state.updates == []


@pytest.mark.asyncio
async def test_relational_loader_mark_sync_date():
    sync_state = FakeSyncStateStore()
    loader = RelationalLoader(
        tenant_id="seller_a",
        model=FakeModel,
        sync_state_store=sync_state,
        record_writer=FakeRecordWriter(),
        log_summary_entry=LogSummaryEntry(entity_name="Fake", action_type=LogActionTypeEnum.LOADER),
        is_debug=False,
    )
    await loader.mark_sync_date(datetime(2024, 6, 15))
    assert sync_state.updates == [("seller_a", {"fake_entity": "2024-06-15"})]
