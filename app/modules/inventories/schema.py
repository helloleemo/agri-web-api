from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class InventoryBalanceResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str | None = None
    unit_id: uuid.UUID
    unit_name: str | None = None
    initial_stock: int
    actual_stock: int
    reserved_stock: int
    available_stock: int
    manual_adjustment_stock: int
    updated_at: datetime


class InventoryManualAdjustRequest(BaseModel):
    product_id: uuid.UUID
    unit_id: uuid.UUID
    delta: int = Field(..., ne=0)
    note: str | None = Field(default=None, max_length=500)


class InventoryLedgerResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str | None = None
    unit_id: uuid.UUID
    unit_name: str | None = None
    order_id: uuid.UUID | None = None
    order_item_id: uuid.UUID | None = None
    action: str
    quantity: int
    delta_actual: int
    delta_reserved: int
    actual_after: int
    reserved_after: int
    available_after: int
    from_order_status_code: int | None = None
    to_order_status_code: int | None = None
    operator_user_id: uuid.UUID | None = None
    note: str | None = None
    created_at: datetime
