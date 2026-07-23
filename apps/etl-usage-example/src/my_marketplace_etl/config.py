from datetime import datetime
from typing import Annotated

from etl_core.config import CoreSettings
from etl_core.entities.enum import SyncType
from pydantic import field_validator
from pydantic_settings import NoDecode, SettingsConfigDict


class Settings(CoreSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore")

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DATABASE_NAME: str = "marketplace_etl"

    MOCK_SOURCE_API_URL: str = "http://localhost:8080"

    SOURCE_PRODUCT_BACKEND: str = "mysql"
    SOURCE_SQLITE_PATH: str = "./data/sqlite_source/marketplace_source.db"

    SOURCE_MYSQL_HOST: str = "localhost"
    SOURCE_MYSQL_PORT: int = 3306
    SOURCE_MYSQL_USER: str = "source"
    SOURCE_MYSQL_PASSWORD: str = "source"
    SOURCE_MYSQL_DATABASE: str = "marketplace_source"

    TARGET_DB_BACKEND: str = "postgres"
    TARGET_DB_SQLITE_BASE_PATH: str = "./data/sqlite"

    MAX_RUNNER_EXECUTIONS: int = 5
    MAX_RUNNER_PARALLEL_EXECUTIONS: int = 10

    APP_SELLERS_TO_RUN: Annotated[list[str], NoDecode] = []
    APP_SELLERS_TO_IGNORE: Annotated[list[str], NoDecode] = []
    APP_ENTITIES_TO_RUN: Annotated[list[str], NoDecode] = []
    APP_SYNC_TYPE: str = SyncType.ALL.value
    APP_PERIODS_TO_RUN: Annotated[tuple[str, str] | None, NoDecode] = None
    APP_CUSTOM_SYNC_INTERVALS: dict[str, int] = {
        "order": 7,
        "product": 7,
        "traffic": 3,
    }
    APP_CUSTOM_UPDATE_ROUTINE: dict = {
        "products": {
            "ignore_columns_to_update_on_upsert": {
                "columns": ["stock_coverage_in_days", "stock", "reserved_stock"],
                "date_operator": {"operator": "lt", "period": {"lower_bound": "today"}},
            }
        }
    }

    @field_validator("APP_SELLERS_TO_RUN", "APP_SELLERS_TO_IGNORE", "APP_ENTITIES_TO_RUN", mode="before")
    @classmethod
    def split_csv(cls, value: str | list[str]) -> list[str]:
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("APP_PERIODS_TO_RUN", mode="before")
    @classmethod
    def decode_periods(cls, value: str | tuple[str, str] | None):
        if not value:
            return None
        if isinstance(value, tuple):
            return value
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError("APP_PERIODS_TO_RUN must have two dates")
        return parts[0], parts[1]


app_settings = Settings()
