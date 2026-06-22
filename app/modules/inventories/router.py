from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import AuthUser, get_auth_context
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.common.messages import CommonMessages
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.common.response import created, ok
from app.modules.common.schema import ApiResponse
from app.modules.inventories import service
from app.modules.inventories.schema import (
    InventoryBalanceResponse,
    InventoryLedgerResponse,
    InventoryManualAdjustRequest,
)
from app.modules.roles.constants import RoleCode

router = APIRouter(prefix="/inventories", tags=["Inventories"])


ADMIN_STAFF_ROLE_CODES = {RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value}


def _ensure_inventory_manage_permission(auth: AuthUser) -> None:
    if auth.role_code not in ADMIN_STAFF_ROLE_CODES:
        raise_error(ErrorCode.FORBIDDEN, detail="Only admin/staff can manage inventory")


@router.get(
    "/balances",
    response_model=ApiResponse[list[InventoryBalanceResponse]],
    response_model_exclude_none=True,
)
def list_inventory_balances(
    pagination: Pagination = Depends(pagination_dep),
    auth: AuthUser = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _ensure_inventory_manage_permission(auth)
    balances = service.list_balances(db, skip=pagination.skip, limit=pagination.limit)
    return ok(balances, CommonMessages.OK)


@router.post(
    "/adjustments",
    response_model=ApiResponse[InventoryBalanceResponse],
    response_model_exclude_none=True,
)
def manual_adjust_inventory(
    payload: InventoryManualAdjustRequest,
    auth: AuthUser = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _ensure_inventory_manage_permission(auth)
    updated = service.adjust_inventory_manually(db, payload=payload, operator_user_id=auth.id)
    return created(updated, "inventory adjusted")


@router.get(
    "/ledger",
    response_model=ApiResponse[list[InventoryLedgerResponse]],
    response_model_exclude_none=True,
)
def list_inventory_ledger(
    pagination: Pagination = Depends(pagination_dep),
    product_id: uuid.UUID | None = Query(default=None),
    unit_id: uuid.UUID | None = Query(default=None),
    order_id: uuid.UUID | None = Query(default=None),
    auth: AuthUser = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _ensure_inventory_manage_permission(auth)
    entries = service.list_ledger(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        product_id=product_id,
        unit_id=unit_id,
        order_id=order_id,
    )
    return ok(entries, CommonMessages.OK)
