from loguru import logger


class StdoutLogSink:
    def info(self, message: str, **context) -> None:
        logger.info(message)

    def error(self, message: str, **context) -> None:
        logger.error(message)

    def success(self, message: str, **context) -> None:
        logger.success(message)
