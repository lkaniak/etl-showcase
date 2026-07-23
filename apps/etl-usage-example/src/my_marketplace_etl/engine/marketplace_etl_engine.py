from datetime import date, datetime

from etl_core.common.data.date_handler import apply_date_offset, get_oldest_sync_date
from etl_core.common.data.string_handler import date_to_str, get_tenant_logger_header
from etl_core.common.logging.logger import LogSummaryEntry, log_error, log_execution, log_info, log_success
from etl_core.engine.base_engine import BaseEngine
from etl_core.entities.enum import LogActionTypeEnum, SyncType
from etl_core.ports.sync_state_store import SyncStateStore
from my_marketplace_etl.adapters.http.mock_source_api_client import MockSourceApiClient
from my_marketplace_etl.adapters.mysql.product_db_reader import MysqlProductDbReader
from my_marketplace_etl.config import app_settings
from my_marketplace_etl.entities.seller_entities import SellerEntity
from my_marketplace_etl.modules.processors import marketplace_dependencies, marketplace_processors
from my_marketplace_etl.ports.loader_factory import LoaderFactory


class MarketplaceEtlEngine(BaseEngine):
    def __init__(
        self,
        seller: SellerEntity,
        sync_dates: dict[str, str],
        retention_period_data: str,
        loader_factory: LoaderFactory,
        sync_state_store: SyncStateStore,
        order_source: MockSourceApiClient | None = None,
        traffic_source: MockSourceApiClient | None = None,
        product_source: MysqlProductDbReader | None = None,
        uuid: str = "",
        sync_type: SyncType = SyncType.ALL,
    ) -> None:
        self.uuid = uuid
        self.seller = seller
        self.sync_type = sync_type
        self.retention_period_data = retention_period_data
        self.loader_factory = loader_factory
        self.sync_state_store = sync_state_store
        self.order_source = order_source or MockSourceApiClient()
        self.traffic_source = traffic_source or MockSourceApiClient()
        self.product_source = product_source or MysqlProductDbReader()
        self.sync_dates = sync_dates
        self.log_summary_entry = LogSummaryEntry(entity_name="MarketplaceEtlEngine", action_type=LogActionTypeEnum.ENGINE)
        self.configure()

    def __repr__(self):
        return "MarketplaceEtlEngine"

    def __get_sync_date_str(self, entity_name: str) -> str:
        if app_settings.APP_PERIODS_TO_RUN:
            return app_settings.APP_PERIODS_TO_RUN[0]
        dependencies = marketplace_dependencies.get(entity_name, [])
        if dependencies:
            _, sync_date_str = get_oldest_sync_date(
                self.sync_dates, dependencies + [entity_name]
            )
        else:
            sync_date_str = self.sync_dates.get(entity_name, "")
        return sync_date_str

    def __is_entity_valid_for_sync_type(self, entity_name: str) -> bool:
        sync_date = self.sync_dates.get(entity_name, "")
        if self.sync_type == SyncType.INCREMENTAL:
            return bool(sync_date)
        if self.sync_type == SyncType.FIRST:
            return not bool(sync_date)
        return True

    @log_execution()
    def configure(self):
        self.runners = []
        today = datetime(year=date.today().year, month=date.today().month, day=date.today().day)
        entities = marketplace_processors.items()
        if app_settings.APP_ENTITIES_TO_RUN:
            entities = [(name, marketplace_processors[name]) for name in app_settings.APP_ENTITIES_TO_RUN]
        for entity_name, Processor in entities:
            sync_date = self.__get_sync_date_str(entity_name)
            if not app_settings.APP_PERIODS_TO_RUN:
                if sync_date:
                    sync_date = date_to_str(
                        apply_date_offset(datetime.fromisoformat(sync_date), app_settings.APP_CUSTOM_SYNC_INTERVALS[entity_name])
                    )
                else:
                    sync_date = self.retention_period_data
            if not self.__is_entity_valid_for_sync_type(entity_name):
                log_info(
                    "MarketplaceEtlEngine",
                    LogActionTypeEnum.ENGINE,
                    f"{get_tenant_logger_header(self)} Skipping {Processor.__name__} for sync type {self.sync_type.value}",
                )
                continue
            source = self.order_source
            if entity_name == "traffic":
                source = self.traffic_source
            elif entity_name == "product":
                source = self.product_source
            self.runners.append(
                Processor(
                    last_sync_date=sync_date,
                    seller=self.seller,
                    source=source,
                    stop_date=(
                        today
                        if not app_settings.APP_PERIODS_TO_RUN
                        else datetime.fromisoformat(app_settings.APP_PERIODS_TO_RUN[1])
                    ),
                    loader_factory=self.loader_factory,
                    sync_state_store=self.sync_state_store,
                )
            )
            log_success(
                "MarketplaceEtlEngine",
                LogActionTypeEnum.ENGINE,
                f"{get_tenant_logger_header(self)} Configured {Processor.__name__}",
            )
