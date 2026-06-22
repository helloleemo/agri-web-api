from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.coupons.constants import CouponDiscountType


class CouponBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=120)
    discount_type: CouponDiscountType
    discount_value: int = Field(..., ge=0)
    min_order_amount: int | None = Field(default=None, ge=0)
    max_discount_amount: int | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status_code: int = Field(default=1, ge=1)


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    discount_type: CouponDiscountType | None = None
    discount_value: int | None = Field(default=None, ge=0)
    min_order_amount: int | None = Field(default=None, ge=0)
    max_discount_amount: int | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status_code: int | None = Field(default=None, ge=1)


class CouponResponse(CouponBase):
    id: uuid.UUID
    used_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
