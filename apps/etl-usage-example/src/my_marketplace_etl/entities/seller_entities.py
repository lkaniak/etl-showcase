from pydantic import BaseModel, Field

from my_marketplace_etl.entities.sync_dates_entity import SyncDatesEntity


class SellerEntity(BaseModel):
    id: str = ""
    name: str = ""
    relational_database_name: str = ""
    is_active: bool = True


class SellerConnectorConfigEntity(BaseModel):
    seller_id: str = ""
    is_active: bool = True
    retention_period_data: str = "2024-01-01"


class SellerPreferencesEntity(BaseModel):
    seller_id: str = ""
    timezone: str = "America/Sao_Paulo"


class EtlSettingsEntity(BaseModel):
    seller_id: str = ""
    sync_dates: SyncDatesEntity = Field(default_factory=SyncDatesEntity)
    sync_status: str = "available"
