from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemBase(BaseModel):
	product_id: uuid.UUID
	unit: str = Field(..., max_length=20)
	quantity: int = Field(default=1, ge=1)


class OrderItemCreate(OrderItemBase):
	pass

class OrderItemUpdate(OrderItemBase):
	pass


class OrderItemResponse(BaseModel):
	id: uuid.UUID
	order_id: uuid.UUID
	product_id: uuid.UUID
	quantity: int
	product_name: str | None = None
	unit: str | None = Field(default=None, max_length=20)

	model_config = ConfigDict(from_attributes=True)


# ----------------------------


class OrderBase(BaseModel):
	user_id: uuid.UUID
	status_code: int = Field(default=1, ge=1)
	order_status_code: int = Field(default=1, ge=1)


class OrderCreate(OrderBase):
	items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
	items: list[OrderItemUpdate] | None = None


class OrderResponse(OrderBase):
	id: uuid.UUID
	order_no: str
	user_name: str | None
	order_status_name: str | None = None
	created_at: datetime
	updated_at: datetime
	items: list[OrderItemResponse]

	model_config = ConfigDict(from_attributes=True)
