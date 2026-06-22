from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CartItemInput(BaseModel):
    product_id: uuid.UUID
    unit_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1)


class CartSyncPayload(BaseModel):
    items: list[CartItemInput]


class CartItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    unit_id: uuid.UUID | None = None
    quantity: int
    product_name: str | None = None
    unit_name: str | None = None
    unit_price: int | None = None
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: uuid.UUID
    items: list[CartItemResponse]

    model_config = ConfigDict(from_attributes=True)
