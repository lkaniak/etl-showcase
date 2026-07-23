from typing import Protocol


class SyncStateStore(Protocol):
    def update_sync_dates(self, tenant_id: str, payload: dict[str, str]) -> None: ...
