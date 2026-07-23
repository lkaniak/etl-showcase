from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseEtlModel(Protocol):
    __tablename__: str
    __syncdateentity__: str
    __uniqueconstraints__: list[str]

    def to_dict(self) -> dict[str, Any]: ...
