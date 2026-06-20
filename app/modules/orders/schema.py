from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.orders.constants import DeliveryMethodCode, PaymentMethodCode


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
	customer_email: str = Field(..., max_length=120)
	customer_name: str | None = Field(default=None, max_length=100)
	address: str | None = Field(default=None, max_length=255)
	coupon_code: str | None = Field(default=None, max_length=50)
	delivery_method: DeliveryMethodCode = Field(default=DeliveryMethodCode.HOME_DELIVERY)
	payment_method: PaymentMethodCode = Field(default=PaymentMethodCode.BANK_TRANSFER)
	orderer_name: str | None = Field(default=None, max_length=100)
	orderer_phone: str | None = Field(default=None, max_length=20)
	orderer_email: str | None = Field(default=None, max_length=120)
	subtotal_amount: int = Field(default=0, ge=0)
	discount_amount: int = Field(default=0, ge=0)
	total_amount: int = Field(default=0, ge=0)
	status_code: int = Field(default=1, ge=1)
	order_status_code: int = Field(default=1, ge=1)


class OrderCreate(OrderBase):
	user_id: uuid.UUID | None = None
	items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
	customer_email: str | None = Field(default=None, max_length=120)
	customer_name: str | None = Field(default=None, max_length=100)
	address: str | None = Field(default=None, max_length=255)
	delivery_method: DeliveryMethodCode | None = Field(default=None)
	payment_method: PaymentMethodCode | None = Field(default=None)
	orderer_name: str | None = Field(default=None, max_length=100)
	orderer_phone: str | None = Field(default=None, max_length=20)
	orderer_email: str | None = Field(default=None, max_length=120)
	status_code: int | None = Field(default=None, ge=1)
	order_status_code: int | None = Field(default=None, ge=1)
	items: list[OrderItemUpdate] | None = None


class OrderAdminNoteUpdate(BaseModel):
	admin_note: str | None = Field(default=None, max_length=500)


class OrderResponse(OrderBase):
	id: uuid.UUID
	order_no: str
	user_id: uuid.UUID
	user_name: str | None
	order_status_name: str | None = None
	delivery_method_label: str | None = None
	payment_method_label: str | None = None
	admin_note: str | None = None
	created_at: datetime
	updated_at: datetime
	items: list[OrderItemResponse]

	model_config = ConfigDict(from_attributes=True)
