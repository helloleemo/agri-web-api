import uuid

from pydantic import BaseModel, ConfigDict


class OrderStatusResponse(BaseModel):
    id: uuid.UUID
    code: int
    name: str

    model_config = ConfigDict(from_attributes=True)
