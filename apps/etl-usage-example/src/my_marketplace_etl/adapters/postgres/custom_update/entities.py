from pydantic import BaseModel, Field


class DateOperatorPeriod(BaseModel):
    lower_bound: str | None = None
    upper_bound: str | None = None


class DateOperatorConfig(BaseModel):
    operator: str = "lt"
    period: DateOperatorPeriod = Field(default_factory=DateOperatorPeriod)


class IgnoreColumnsToUpdateOnUpsertMetadata(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    get_row_hash: object
    table_name: str
    primary_keys: list[str]
    data_columns: list[str]


class IgnoreColumnsToUpdateOnUpsertParams(BaseModel):
    columns: list[str]
    date_operator: DateOperatorConfig = Field(default_factory=DateOperatorConfig)
