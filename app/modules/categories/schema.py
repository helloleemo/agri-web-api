

from datetime import datetime
import uuid

from pydantic import BaseModel
from pydantic import Field, ConfigDict


class CategoryBase(BaseModel):
    name: str

class CreateCategory(CategoryBase):
    pass

class UpdateCategory(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: uuid.UUID
    meta_data: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
