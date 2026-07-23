#!/usr/bin/env python3
import os

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "marketplace_etl"

SELLERS = [
    {
        "_id": "seller_a",
        "id": "seller_a",
        "name": "Seller Alpha",
        "relational_database_name": "seller_a_db",
        "is_active": True,
    },
    {
        "_id": "seller_b",
        "id": "seller_b",
        "name": "Seller Beta",
        "relational_database_name": "seller_b_db",
        "is_active": True,
    },
]


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    db.sellers.delete_many({})
    db.seller_connector_config.delete_many({})
    db.seller_preferences.delete_many({})
    db.seller_etl_settings.delete_many({})

    for seller in SELLERS:
        db.sellers.insert_one(seller)
        db.seller_connector_config.insert_one(
            {"seller_id": seller["id"], "is_active": True, "retention_period_data": "2024-01-01"}
        )
        db.seller_preferences.insert_one({"seller_id": seller["id"], "timezone": "America/Sao_Paulo"})
        db.seller_etl_settings.insert_one(
            {
                "seller_id": seller["id"],
                "sync_status": "available",
                "sync_dates": {
                    "order": "",
                    "order_payment": "",
                    "product": "",
                    "traffic": "",
                },
            }
        )
    print(f"Seeded MongoDB at {MONGO_URI}/{DB_NAME}")


if __name__ == "__main__":
    main()
