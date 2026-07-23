from typing import Protocol

from my_marketplace_etl.entities.seller_entities import (
    EtlSettingsEntity,
    SellerConnectorConfigEntity,
    SellerEntity,
)


class ConfigStore(Protocol):
    def get_eligible_sellers(
        self, include: list[str], exclude: list[str]
    ) -> list[SellerConnectorConfigEntity]: ...

    def get_seller(self, seller_id: str) -> SellerEntity: ...

    def get_etl_settings(self, seller_id: str) -> EtlSettingsEntity: ...

    def set_sync_status(self, seller_id: str, status: str) -> None: ...
