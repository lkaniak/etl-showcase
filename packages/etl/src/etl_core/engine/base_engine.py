import asyncio
from abc import ABCMeta, abstractmethod

from etl_core.common.data.string_handler import get_tenant_logger_header
from etl_core.common.logging.logger import log_error, log_execution_async, log_success
from etl_core.entities.exceptions.multiple_exception import MultipleExceptions
from etl_core.infra.concurrency.parallelism import runner_worker
from etl_core.modules.base.base_processor import BaseProcessor


class BaseEngine(metaclass=ABCMeta):
    processors: dict[str, BaseProcessor] = {}

    @abstractmethod
    def configure(self):
        pass

    @log_execution_async()
    async def initialize(self):
        runner_tasks = []
        for runner in self.runners:
            runner_task_name = (
                f"{get_tenant_logger_header(self)} ETL Runner {runner.__class__.__name__}"
            )
            try:
                runner_task = asyncio.ensure_future(runner_worker(runner_task_name, runner))
                log_success(
                    entity_name=self.log_summary_entry.entity_name,
                    action_type=self.log_summary_entry.action_type,
                    message=f"{get_tenant_logger_header(self)} Added runner {runner_task_name}",
                )
                runner_tasks.append(runner_task)
            except Exception as e:
                log_error(
                    entity_name=self.log_summary_entry.entity_name,
                    action_type=self.log_summary_entry.action_type,
                    message=f"{get_tenant_logger_header(self)} Error with runner {runner_task_name}: {e}",
                )
        done, _ = await asyncio.wait(runner_tasks, return_when=asyncio.ALL_COMPLETED)
        exceptions = [task.exception() for task in done if task.exception() is not None]
        if exceptions:
            raise MultipleExceptions.handle_multiple_exceptions(exceptions)
