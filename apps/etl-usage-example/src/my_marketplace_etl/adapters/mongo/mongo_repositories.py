import os

from pymongo import MongoClient

from my_marketplace_etl.config import app_settings
from my_marketplace_etl.entities.seller_entities import (
    EtlSettingsEntity,
    SellerConnectorConfigEntity,
    SellerEntity,
    SellerPreferencesEntity,
)
from my_marketplace_etl.entities.sync_dates_entity import SyncDatesEntity
from my_marketplace_etl.ports.config_store import ConfigStore


class MongoConfigStore(ConfigStore):
    def __init__(self):
        self.client = MongoClient(app_settings.MONGO_URI)
        self.db = self.client[app_settings.MONGO_DATABASE_NAME]

    def get_eligible_sellers(
        self, include: list[str], exclude: list[str]
    ) -> list[SellerConnectorConfigEntity]:
        query: dict = {"is_active": True}
        if include:
            query["seller_id"] = {"$in": include}
        if exclude:
            query.setdefault("seller_id", {})
            query["seller_id"]["$nin"] = exclude
        return [
            SellerConnectorConfigEntity(**doc)
            for doc in self.db.seller_connector_config.find(query)
        ]

    def get_seller(self, seller_id: str) -> SellerEntity:
        doc = self.db.sellers.find_one({"_id": seller_id}) or self.db.sellers.find_one({"id": seller_id})
        if not doc:
            raise ValueError(f"Seller {seller_id} not found")
        return SellerEntity(
            id=str(doc.get("_id", doc.get("id", seller_id))),
            name=doc.get("name", ""),
            relational_database_name=doc.get("relational_database_name", f"seller_{seller_id}_db"),
            is_active=doc.get("is_active", True),
        )

    def get_etl_settings(self, seller_id: str) -> EtlSettingsEntity:
        doc = self.db.seller_etl_settings.find_one({"seller_id": seller_id})
        if not doc:
            return EtlSettingsEntity(seller_id=seller_id)
        sync_dates = SyncDatesEntity(**doc.get("sync_dates", {}))
        return EtlSettingsEntity(
            seller_id=seller_id,
            sync_dates=sync_dates,
            sync_status=doc.get("sync_status", "available"),
        )

    def set_sync_status(self, seller_id: str, status: str) -> None:
        self.db.seller_etl_settings.update_one(
            {"seller_id": seller_id},
            {"$set": {"sync_status": status}},
            upsert=True,
        )


class MongoSyncStateStore:
    def __init__(self, client: MongoClient | None = None):
        self.client = client or MongoClient(app_settings.MONGO_URI)
        self.db = self.client[app_settings.MONGO_DATABASE_NAME]

    def update_sync_dates(self, tenant_id: str, payload: dict[str, str]) -> None:
        current = self.db.seller_etl_settings.find_one({"seller_id": tenant_id}) or {}
        sync_dates = current.get("sync_dates", {})
        for key, value in payload.items():
            if value:
                sync_dates[key] = value
        self.db.seller_etl_settings.update_one(
            {"seller_id": tenant_id},
            {"$set": {"sync_dates": sync_dates}},
            upsert=True,
        )


def get_seller_preferences(seller_id: str) -> SellerPreferencesEntity:
    client = MongoClient(app_settings.MONGO_URI)
    doc = client[app_settings.MONGO_DATABASE_NAME].seller_preferences.find_one({"seller_id": seller_id})
    if not doc:
        return SellerPreferencesEntity(seller_id=seller_id)
    return SellerPreferencesEntity(**doc)
