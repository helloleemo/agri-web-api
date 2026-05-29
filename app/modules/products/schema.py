from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(default="other", max_length=60)
    origin: str | None = Field(default=None, max_length=120)
    unit: str = Field(default="kg", max_length=20)
    price: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    description: str | None = None
    status_id: int = Field(default=1, ge=1)
    image: str | None = Field(default=None, max_length=500)
    image_group: list[str] | None = Field(default=None)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=60)
    origin: str | None = Field(default=None, max_length=120)
    unit: str | None = Field(default=None, max_length=20)
    price: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    description: str | None = None
    image: str | None = Field(default=None, max_length=500)
    image_group: list[str] | None = Field(default=None)
    status_id: int | None = None

class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)