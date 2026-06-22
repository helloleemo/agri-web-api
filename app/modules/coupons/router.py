from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.common.messages import CouponMessages
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.common.response import ok
from app.modules.common.schema import ApiResponse
from app.modules.coupons import service
from app.modules.coupons.schema import CouponCreate, CouponResponse, CouponUpdate
from app.modules.roles.constants import RoleCode


router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.get("", response_model=ApiResponse[list[CouponResponse]], response_model_exclude_none=True)
def list_coupons(
    pagination: Pagination = Depends(pagination_dep),
    db: Session = Depends(get_db),
):
    coupons = service.list_coupons(db)
    start = pagination.skip
    end = pagination.skip + pagination.limit
    return ok(coupons[start:end], CouponMessages.LIST)


@router.get("/{coupon_id}", response_model=ApiResponse[CouponResponse], response_model_exclude_none=True)
def get_coupon(coupon_id: uuid.UUID, db: Session = Depends(get_db)):
    coupon = service.get_coupon_by_id(db, coupon_id)
    if not coupon:
        raise_error(ErrorCode.NOT_FOUND, detail=f"Coupon not found: {coupon_id}")
    return ok(coupon, CouponMessages.GET)


@router.post(
    "",
    response_model=ApiResponse[CouponResponse],
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def create_coupon(payload: CouponCreate, db: Session = Depends(get_db)):
    coupon = service.create_coupon(db, payload)
    return ok(coupon, CouponMessages.CREATE)


@router.patch(
    "/{coupon_id}",
    response_model=ApiResponse[CouponResponse],
    response_model_exclude_none=True,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def update_coupon(coupon_id: uuid.UUID, payload: CouponUpdate, db: Session = Depends(get_db)):
    updated = service.update_coupon(db, coupon_id, payload)
    if not updated:
        raise_error(ErrorCode.NOT_FOUND, detail=f"Coupon not found: {coupon_id}")
    return ok(updated, CouponMessages.UPDATE)


@router.delete(
    "/{coupon_id}",
    response_model=ApiResponse[dict[str, str]],
    response_model_exclude_none=True,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def delete_coupon(coupon_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted = service.delete_coupon(db, coupon_id)
    if not deleted:
        raise_error(ErrorCode.NOT_FOUND, detail=f"Coupon not found: {coupon_id}")
    return ok({"id": str(coupon_id)}, CouponMessages.DELETE)
