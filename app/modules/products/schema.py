from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.modules.statuses.constants import StatusCode


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category_id: uuid.UUID = Field(...)
    category_name: str | None = Field(default=None, max_length=60)
    origin: str | None = Field(default=None, max_length=120)
    unit: str = Field(default="kg", max_length=20)
    price: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    description: str | None = None
    image: str | None = Field(default=None, max_length=500)
    image_group: list[str] | None = Field(default=None)
    status_code: StatusCode = Field(default=StatusCode.ENABLED)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase): # 全部改成部分更新
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category_id: uuid.UUID | None = Field(default=None)
    origin: str | None = Field(default=None, max_length=120)
    unit: str | None = Field(default=None, max_length=20)
    price: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    description: str | None = None
    image: str | None = Field(default=None, max_length=500)
    image_group: list[str] | None = Field(default=None)
    status_code: StatusCode | None = None

class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 
    # 允許從 ORM 模型的屬性讀取資料，而不僅僅是從字典鍵讀取。這對於與 SQLAlchemy 等 ORM 工具一起使用非常有用，因為它們通常使用屬性而不是字典來表示模型的字段。