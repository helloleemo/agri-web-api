from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemBase(BaseModel):
	product_id: uuid.UUID
	quantity: int = Field(default=1, ge=1)
	status_id: int = Field(default=1, ge=1)


class OrderItemCreate(OrderItemBase):
	pass


class OrderItemUpdate(BaseModel):
	product_id: uuid.UUID | None = None
	product_name: str | None = None
	quantity: int | None = Field(default=None, ge=1)
	status_id: int | None = Field(default=None, ge=1)


class OrderItemResponse(OrderItemBase):
	id: uuid.UUID
	order_id: uuid.UUID
	product_name: str | None = None

	model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
	user_id: uuid.UUID
	status_id: int = Field(default=1, ge=1)


class OrderCreate(OrderBase):
	items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
	status_id: int | None = Field(default=None, ge=1)
	items: list[OrderItemCreate] | None = None


class OrderResponse(OrderBase):
	id: uuid.UUID
	created_at: datetime
	updated_at: datetime
	items: list[OrderItemResponse]

	model_config = ConfigDict(from_attributes=True)
