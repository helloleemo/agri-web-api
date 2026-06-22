

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ImageBase(BaseModel):
    product_id: uuid.UUID = Field(...)
    is_primary: bool = Field(default=False)
    sort_order: int = Field(default=0, ge=0)


class ImageCreate(ImageBase):
    pass


class ImageUpdate(BaseModel):
    is_primary: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class ImageResponse(ImageBase):
    id: uuid.UUID = Field(...)
    stored_filename: str = Field(..., max_length=300)
    file_url: str = Field(..., max_length=300)
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)
