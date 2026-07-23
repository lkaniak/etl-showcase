from enum import Enum


class SyncType(Enum):
    FIRST = "first"
    INCREMENTAL = "incremental"
    ALL = "all"


class SyncStatusType(Enum):
    PROCESSING = "processing"
    AVAILABLE = "available"
