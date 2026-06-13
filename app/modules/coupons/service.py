from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import NoReturn

from sqlalchemy.orm import Session

from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.coupons import crud
from app.modules.coupons.constants import CouponDiscountType
from app.modules.coupons.model import Coupon
from app.modules.coupons.schema import CouponCreate, CouponResponse, CouponUpdate
from app.modules.statuses.constants import StatusCode


def _raise_bad_request(detail: str) -> NoReturn:
    raise_error(ErrorCode.BAD_REQUEST, detail=detail)  # type: ignore[arg-type]


def _raise_conflict(detail: str) -> NoReturn:
    raise_error(ErrorCode.CONFLICT, detail=detail)  # type: ignore[arg-type]


def _to_coupon_response(coupon: Coupon) -> CouponResponse:
    return CouponResponse(
        id=coupon.id,
        code=coupon.code,
        name=coupon.name,
        discount_type=CouponDiscountType(coupon.discount_type),
        discount_value=coupon.discount_value,
        min_order_amount=coupon.min_order_amount,
        max_discount_amount=coupon.max_discount_amount,
        usage_limit=coupon.usage_limit,
        starts_at=coupon.starts_at,
        ends_at=coupon.ends_at,
        status_code=coupon.status_code,
        used_count=coupon.used_count,
        created_at=coupon.created_at,
        updated_at=coupon.updated_at,
    )


def _validate_coupon_payload(data: CouponCreate | CouponUpdate) -> None:
    discount_type = getattr(data, "discount_type", None)
    discount_value = getattr(data, "discount_value", None)
    if discount_type == CouponDiscountType.PERCENT and discount_value is not None:
        if discount_value <= 0 or discount_value > 100:
            _raise_bad_request("Percent coupon discount_value must be between 1 and 100")

    starts_at = getattr(data, "starts_at", None)
    ends_at = getattr(data, "ends_at", None)
    if starts_at and ends_at and starts_at > ends_at:
        _raise_bad_request("Coupon starts_at must be earlier than ends_at")


def list_coupons(db: Session) -> list[CouponResponse]:
    coupons = crud.get_coupons(db)
    return [_to_coupon_response(coupon) for coupon in coupons]


def get_coupon_by_id(db: Session, coupon_id: uuid.UUID) -> CouponResponse | None:
    coupon = crud.get_coupon_by_id(db, coupon_id)
    if not coupon:
        return None
    return _to_coupon_response(coupon)


def create_coupon(db: Session, data: CouponCreate) -> CouponResponse:
    existing = crud.get_coupon_by_code(db, data.code)
    if existing:
        _raise_conflict(f"Coupon code already exists: {data.code}")

    _validate_coupon_payload(data)
    coupon = crud.create_coupon(db, data)
    return _to_coupon_response(coupon)


def update_coupon(db: Session, coupon_id: uuid.UUID, data: CouponUpdate) -> CouponResponse | None:
    coupon = crud.get_coupon_by_id(db, coupon_id)
    if not coupon:
        return None

    _validate_coupon_payload(data)
    updated = crud.update_coupon(db, coupon, data)
    return _to_coupon_response(updated)


def delete_coupon(db: Session, coupon_id: uuid.UUID) -> bool:
    coupon = crud.get_coupon_by_id(db, coupon_id)
    if not coupon:
        return False
    crud.delete_coupon(db, coupon)
    return True


def apply_coupon(db: Session, coupon_code: str, subtotal_amount: int) -> tuple[Coupon, int]:
    normalized = coupon_code.strip().upper()
    coupon = crud.get_coupon_by_code(db, normalized)
    if not coupon:
        _raise_bad_request(f"Invalid coupon code: {coupon_code}")

    if coupon.status_code != StatusCode.ENABLED.value:
        _raise_bad_request(f"Coupon is not enabled: {coupon_code}")

    now = datetime.now(timezone.utc)
    if coupon.starts_at and coupon.starts_at > now:
        _raise_bad_request(f"Coupon is not active yet: {coupon_code}")
    if coupon.ends_at and coupon.ends_at < now:
        _raise_bad_request(f"Coupon expired: {coupon_code}")

    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        _raise_bad_request(f"Coupon usage limit reached: {coupon_code}")

    if coupon.min_order_amount is not None and subtotal_amount < coupon.min_order_amount:
        _raise_bad_request(f"Order amount does not meet coupon minimum: {coupon.min_order_amount}")

    discount = 0
    if coupon.discount_type == CouponDiscountType.FIXED.value:
        discount = coupon.discount_value
    elif coupon.discount_type == CouponDiscountType.PERCENT.value:
        discount = subtotal_amount * coupon.discount_value // 100
    else:
        _raise_bad_request(f"Invalid coupon discount type: {coupon.discount_type}")

    if coupon.max_discount_amount is not None:
        discount = min(discount, coupon.max_discount_amount)

    discount = max(0, min(discount, subtotal_amount))
    crud.increase_coupon_used_count(db, coupon)
    return coupon, discount
