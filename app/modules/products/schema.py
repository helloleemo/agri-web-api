from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.modules.images.schema import ImageResponse
from app.modules.statuses.constants import StatusCode


class ProductUnitBase(BaseModel):
    unit_id: uuid.UUID
    price: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)


class ProductUnitCreate(ProductUnitBase):
    pass


class ProductUnitUpdate(ProductUnitBase):
    pass


class ProductUnitResponse(ProductUnitBase):
    unit_name: str | None = Field(default=None, max_length=20)

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    name: str = Field(..., min_length=1, max_length=120)
    category_id: uuid.UUID = Field(...)
    category_name: str | None = Field(default=None, max_length=60)
    origin: str | None = Field(default=None, max_length=120)
    description: str | None = None
    images: list[ImageResponse] | None = None
    # image: str | None = Field(default=None, max_length=500)
    # image_group: list[str] | None = Field(default=None)
    status_code: StatusCode = Field(default=StatusCode.ENABLED)


class ProductCreate(ProductBase):
    units: list[ProductUnitCreate] = Field(..., min_length=1)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    category_id: uuid.UUID | None = Field(default=None)
    category_name: str | None = Field(default=None, max_length=60)
    origin: str | None = Field(default=None, max_length=120)
    description: str | None = None
    images: list[ImageResponse] | None = None
    # image: str | None = Field(default=None, max_length=500)
    # image_group: list[str] | None = Field(default=None)
    status_code: StatusCode | None = None
    units: list[ProductUnitUpdate] | None = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    units: list[ProductUnitResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    # 允許從 ORM 模型的屬性讀取資料，而不僅僅是從字典鍵讀取。這對於與 SQLAlchemy 等 ORM 工具一起使用非常有用，因為它們通常使用屬性而不是字典來表示模型的字段。