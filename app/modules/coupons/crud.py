from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.coupons.model import Coupon
from app.modules.coupons.schema import CouponCreate, CouponUpdate
from app.modules.statuses.constants import StatusCode


def get_coupon_by_id(db: Session, coupon_id: uuid.UUID) -> Coupon | None:
    return db.scalar(select(Coupon).where(Coupon.id == coupon_id))


def get_coupon_by_code(db: Session, code: str) -> Coupon | None:
    return db.scalar(select(Coupon).where(Coupon.code == code))


def get_coupons(db: Session) -> list[Coupon]:
    stmt = select(Coupon).where(Coupon.status_code != StatusCode.DELETED.value)
    return list(db.scalars(stmt).all())


def create_coupon(db: Session, data: CouponCreate) -> Coupon:
    payload = data.model_dump(mode="python")
    new_coupon = Coupon(**payload)
    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)
    return new_coupon


def update_coupon(db: Session, coupon: Coupon, data: CouponUpdate) -> Coupon:
    payload = data.model_dump(mode="python", exclude_unset=True)
    for field, value in payload.items():
        setattr(coupon, field, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    coupon.status_code = StatusCode.DELETED.value
    db.commit()


def increase_coupon_used_count(db: Session, coupon: Coupon) -> Coupon:
    coupon.used_count += 1
    db.flush()
    return coupon
