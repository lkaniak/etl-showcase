from pydantic import BaseModel, Field


class SyncDatesEntity(BaseModel):
    order: str = ""
    order_payment: str = ""
    product: str = ""
    traffic: str = ""

    def model_dump(self, **kwargs):
        return super().model_dump(**kwargs)
