from pydantic import BaseModel

from etl_core.modules.base.base_loader import BaseLoader
from etl_core.modules.base.base_transformer import BaseTransformer


class EtlProcessorEntity(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str
    transformer: BaseTransformer
    loader: BaseLoader
    payload: list
