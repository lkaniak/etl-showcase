from etl_core.entities.exceptions.app_exception import AppException


class MultipleExceptions(Exception):
    exceptions: list[Exception]

    def __init__(self, exceptions: list[Exception]):
        self.exceptions = exceptions

    def __str__(self):
        errors = [str(exception) for exception in self.exceptions]
        return f"Multiple errors occurred: {'; '.join(errors)}"

    @classmethod
    def handle_multiple_exceptions(cls, exceptions: list[Exception]):
        if len(exceptions) == 1:
            return exceptions[0]
        if len(exceptions) > 1:
            return MultipleExceptions(exceptions=exceptions)
        return None
