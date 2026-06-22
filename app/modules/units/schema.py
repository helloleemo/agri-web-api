from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class UnitBase(BaseModel):
    name: str


class CreateUnit(UnitBase):
    pass


class UpdateUnit(UnitBase):
    pass


class UnitResponse(UnitBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
