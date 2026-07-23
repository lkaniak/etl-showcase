import asyncio
from functools import wraps
import datetime
import time

from loguru import logger
from pydantic import BaseModel

from etl_core.common.data.string_handler import get_tenant_logger_header
from etl_core.entities.enum import LogActionTypeEnum, LogExecutionStatusEnum

logs_summaries: dict[str, "LogSummary"] = {}


class LogSummaryEntry(BaseModel):
    entity_name: str
    action_type: LogActionTypeEnum


class LogEntry(BaseModel):
    log_message: str = ""
    status: LogExecutionStatusEnum = LogExecutionStatusEnum.PROCESSING
    time_elapsed: float = 0


class LogSummary(BaseModel):
    time_elapsed: float = 0
    log_entries: list[LogEntry] = []
    entity_name: str = ""
    action_type: LogActionTypeEnum = LogActionTypeEnum.PROCESSOR

    def __repr__(self):
        return f"{self.entity_name}&&&{self.action_type.value}"

    def __hash__(self):
        return hash(self.__repr__())


def update_log_summary_entry(log_summary_entry: LogSummaryEntry, log_entry: LogEntry):
    key = LogSummary(
        entity_name=log_summary_entry.entity_name,
        action_type=log_summary_entry.action_type,
    ).__repr__()
    if key not in logs_summaries:
        logs_summaries[key] = LogSummary(
            entity_name=log_summary_entry.entity_name,
            action_type=log_summary_entry.action_type,
        )
    logs_summaries[key].log_entries.append(log_entry)
    logs_summaries[key].time_elapsed += log_entry.time_elapsed


def log_error(entity_name: str, action_type: LogActionTypeEnum, message: str, time_elapsed: float = 0):
    logger.error(message)
    update_log_summary_entry(
        LogSummaryEntry(entity_name=entity_name, action_type=action_type),
        LogEntry(log_message=message, status=LogExecutionStatusEnum.ERROR, time_elapsed=time_elapsed),
    )


def log_info(entity_name: str, action_type: LogActionTypeEnum, message: str, time_elapsed: float = 0):
    logger.info(message)
    update_log_summary_entry(
        LogSummaryEntry(entity_name=entity_name, action_type=action_type),
        LogEntry(log_message=message, status=LogExecutionStatusEnum.PROCESSING, time_elapsed=time_elapsed),
    )


def log_success(entity_name: str, action_type: LogActionTypeEnum, message: str, time_elapsed: float = 0):
    logger.success(message)
    update_log_summary_entry(
        LogSummaryEntry(entity_name=entity_name, action_type=action_type),
        LogEntry(log_message=message, status=LogExecutionStatusEnum.SUCCESS, time_elapsed=time_elapsed),
    )


def print_log_execution_summary(limit: int | None = None, filter_entry: LogEntry | None = None):
    entries = [entry for summary in logs_summaries.values() for entry in summary.log_entries]
    if filter_entry and filter_entry.status:
        entries = [e for e in entries if e.status == filter_entry.status]
    entries.sort(key=lambda x: x.time_elapsed, reverse=True)
    if limit:
        entries = entries[:limit]
    for entry in entries:
        logger.debug(f"{entry.status.value}: {entry.log_message} ({entry.time_elapsed:.2f}s)")


def log_execution_async(custom_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            class_name = self.__class__.__name__
            log_summary_entry = self.log_summary_entry
            prefix = get_tenant_logger_header(self) or custom_prefix
            entity_name = log_summary_entry.entity_name
            action_type = log_summary_entry.action_type
            log_info(entity_name, action_type, f"{prefix} Starting {class_name}.{func.__name__}")
            start = time.perf_counter()
            exception = None
            try:
                result = await func(self, *args, **kwargs)
            except Exception as e:
                exception = e
                result = None
            elapsed = time.perf_counter() - start
            log_info(
                entity_name,
                action_type,
                f"{prefix} Finished {class_name}.{func.__name__} in {datetime.timedelta(seconds=elapsed)}",
                elapsed,
            )
            if exception:
                log_error(entity_name, action_type, f"{class_name}.{func.__name__} exception: {exception}", elapsed)
                raise exception
            log_success(entity_name, action_type, f"{class_name}.{func.__name__} completed", elapsed)
            return result

        return wrapper

    return decorator


def log_execution(custom_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            class_name = self.__class__.__name__
            log_summary_entry = self.log_summary_entry
            prefix = get_tenant_logger_header(self) or custom_prefix
            entity_name = log_summary_entry.entity_name
            action_type = log_summary_entry.action_type
            log_info(entity_name, action_type, f"{prefix} Starting {class_name}.{func.__name__}")
            start = time.perf_counter()
            exception = None
            try:
                result = func(self, *args, **kwargs)
            except Exception as e:
                exception = e
                result = None
            elapsed = time.perf_counter() - start
            if exception:
                log_error(entity_name, action_type, f"{class_name}.{func.__name__} exception: {exception}", elapsed)
                raise exception
            log_success(entity_name, action_type, f"{class_name}.{func.__name__} completed", elapsed)
            return result

        return wrapper

    return decorator
