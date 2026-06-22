from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.inventories import crud
from app.modules.inventories.constants import InventoryLedgerAction
from app.modules.inventories.model import InventoryBalance, InventoryLedger
from app.modules.inventories.schema import (
    InventoryBalanceResponse,
    InventoryLedgerResponse,
    InventoryManualAdjustRequest,
)
from app.modules.order_statuses.constants import OrderStatusCode
from app.modules.orders.model import Order, OrderItem
from app.modules.products.model import ProductUnits
from app.modules.units.model import Unit


RESERVED_STATUS_CODES = {
    OrderStatusCode.ORDER_CREATED.value,
    OrderStatusCode.ORDER_CONFIRMED_AND_PENDING_PAYMENT.value,
    OrderStatusCode.PAID_AND_PREPARING.value,
    OrderStatusCode.SHIPPING.value,
}


def _available_stock(balance: InventoryBalance) -> int:
    return balance.actual_stock - balance.reserved_stock


def _to_balance_response(balance: InventoryBalance) -> InventoryBalanceResponse:
    return InventoryBalanceResponse(
        id=balance.id,
        product_id=balance.product_id,
        product_name=getattr(getattr(balance, "product", None), "name", None),
        unit_id=balance.unit_id,
        unit_name=getattr(getattr(balance, "unit", None), "name", None),
        initial_stock=balance.initial_stock,
        actual_stock=balance.actual_stock,
        reserved_stock=balance.reserved_stock,
        available_stock=_available_stock(balance),
        manual_adjustment_stock=balance.manual_adjustment_stock,
        updated_at=balance.updated_at,
    )


def _to_ledger_response(entry: InventoryLedger) -> InventoryLedgerResponse:
    return InventoryLedgerResponse(
        id=entry.id,
        product_id=entry.product_id,
        product_name=getattr(getattr(entry, "product", None), "name", None),
        unit_id=entry.unit_id,
        unit_name=getattr(getattr(entry, "unit", None), "name", None),
        order_id=entry.order_id,
        order_item_id=entry.order_item_id,
        action=entry.action,
        quantity=entry.quantity,
        delta_actual=entry.delta_actual,
        delta_reserved=entry.delta_reserved,
        actual_after=entry.actual_after,
        reserved_after=entry.reserved_after,
        available_after=entry.available_after,
        from_order_status_code=entry.from_order_status_code,
        to_order_status_code=entry.to_order_status_code,
        operator_user_id=entry.operator_user_id,
        note=entry.note,
        created_at=entry.created_at,
    )


def _resolve_unit_id_for_order_item(db: Session, item: OrderItem) -> uuid.UUID:
    if item.unit_id is not None:
        return item.unit_id

    if item.unit:
        unit_id = db.scalar(
            select(ProductUnits.unit_id)
            .join(Unit, Unit.id == ProductUnits.unit_id)
            .where(ProductUnits.product_id == item.product_id, Unit.name == item.unit)
            .limit(1)
        )
        if unit_id is not None:
            return unit_id

    candidate_ids = list(
        db.scalars(select(ProductUnits.unit_id).where(ProductUnits.product_id == item.product_id).limit(2)).all()
    )
    if len(candidate_ids) == 1:
        return candidate_ids[0]

    raise_error(
        ErrorCode.ORDER_ITEM_INVALID,
        detail=f"Cannot resolve unit for order item {item.id} product_id={item.product_id}",
    )


def _write_ledger(
    db: Session,
    *,
    balance: InventoryBalance,
    action: InventoryLedgerAction,
    quantity: int,
    delta_actual: int,
    delta_reserved: int,
    order_id: uuid.UUID | None,
    order_item_id: uuid.UUID | None,
    from_status: int | None,
    to_status: int | None,
    operator_user_id: uuid.UUID | None,
    note: str | None,
) -> None:
    crud.create_inventory_ledger(
        db,
        {
            "product_id": balance.product_id,
            "unit_id": balance.unit_id,
            "order_id": order_id,
            "order_item_id": order_item_id,
            "action": action.value,
            "quantity": quantity,
            "delta_actual": delta_actual,
            "delta_reserved": delta_reserved,
            "actual_after": balance.actual_stock,
            "reserved_after": balance.reserved_stock,
            "available_after": _available_stock(balance),
            "from_order_status_code": from_status,
            "to_order_status_code": to_status,
            "operator_user_id": operator_user_id,
            "note": note,
        },
    )


def _apply_reserve(
    db: Session,
    *,
    order: Order,
    order_item: OrderItem,
    unit_id: uuid.UUID,
    operator_user_id: uuid.UUID | None,
    from_status: int | None,
    to_status: int,
) -> None:
    balance = crud.get_inventory_balance_for_update(db, order_item.product_id, unit_id)
    if balance is None:
        raise_error(
            ErrorCode.BAD_REQUEST,
            detail=f"Inventory balance not found for product_id={order_item.product_id}, unit_id={unit_id}",
        )

    if _available_stock(balance) < order_item.quantity:
        raise_error(
            ErrorCode.PRODUCT_OUT_OF_STOCK,
            detail=f"Insufficient available stock for product_id={order_item.product_id}, unit_id={unit_id}",
        )

    balance.reserved_stock += order_item.quantity
    _write_ledger(
        db,
        balance=balance,
        action=InventoryLedgerAction.RESERVE,
        quantity=order_item.quantity,
        delta_actual=0,
        delta_reserved=order_item.quantity,
        order_id=order.id,
        order_item_id=order_item.id,
        from_status=from_status,
        to_status=to_status,
        operator_user_id=operator_user_id,
        note=None,
    )


def _apply_release(
    db: Session,
    *,
    order: Order,
    order_item: OrderItem,
    unit_id: uuid.UUID,
    operator_user_id: uuid.UUID | None,
    from_status: int | None,
    to_status: int,
) -> None:
    balance = crud.get_inventory_balance_for_update(db, order_item.product_id, unit_id)
    if balance is None:
        raise_error(
            ErrorCode.BAD_REQUEST,
            detail=f"Inventory balance not found for product_id={order_item.product_id}, unit_id={unit_id}",
        )

    if balance.reserved_stock < order_item.quantity:
        raise_error(
            ErrorCode.CONFLICT,
            detail=f"Reserved stock underflow for product_id={order_item.product_id}, unit_id={unit_id}",
        )

    balance.reserved_stock -= order_item.quantity
    _write_ledger(
        db,
        balance=balance,
        action=InventoryLedgerAction.RELEASE,
        quantity=order_item.quantity,
        delta_actual=0,
        delta_reserved=-order_item.quantity,
        order_id=order.id,
        order_item_id=order_item.id,
        from_status=from_status,
        to_status=to_status,
        operator_user_id=operator_user_id,
        note=None,
    )


def _apply_commit_deduct(
    db: Session,
    *,
    order: Order,
    order_item: OrderItem,
    unit_id: uuid.UUID,
    operator_user_id: uuid.UUID | None,
    from_status: int | None,
    to_status: int,
) -> None:
    balance = crud.get_inventory_balance_for_update(db, order_item.product_id, unit_id)
    if balance is None:
        raise_error(
            ErrorCode.BAD_REQUEST,
            detail=f"Inventory balance not found for product_id={order_item.product_id}, unit_id={unit_id}",
        )

    if balance.reserved_stock < order_item.quantity:
        raise_error(
            ErrorCode.CONFLICT,
            detail=f"Reserved stock underflow for product_id={order_item.product_id}, unit_id={unit_id}",
        )
    if balance.actual_stock < order_item.quantity:
        raise_error(
            ErrorCode.CONFLICT,
            detail=f"Actual stock underflow for product_id={order_item.product_id}, unit_id={unit_id}",
        )

    balance.reserved_stock -= order_item.quantity
    balance.actual_stock -= order_item.quantity
    _write_ledger(
        db,
        balance=balance,
        action=InventoryLedgerAction.COMMIT_DEDUCT,
        quantity=order_item.quantity,
        delta_actual=-order_item.quantity,
        delta_reserved=-order_item.quantity,
        order_id=order.id,
        order_item_id=order_item.id,
        from_status=from_status,
        to_status=to_status,
        operator_user_id=operator_user_id,
        note=None,
    )


def apply_order_status_transition(
    db: Session,
    *,
    order: Order,
    previous_status_code: int | None,
    new_status_code: int,
    operator_user_id: uuid.UUID | None,
) -> None:
    prev_reserved = previous_status_code in RESERVED_STATUS_CODES if previous_status_code is not None else False
    new_reserved = new_status_code in RESERVED_STATUS_CODES

    if previous_status_code == new_status_code:
        return

    if not prev_reserved and new_reserved:
        action = "reserve"
    elif prev_reserved and new_status_code == OrderStatusCode.DELIVERED.value:
        action = "commit_deduct"
    elif prev_reserved and new_status_code in {OrderStatusCode.CANCELED.value, OrderStatusCode.REFUNDED.value}:
        action = "release"
    else:
        action = "noop"

    if action == "noop":
        return

    for item in order.items:
        unit_id = _resolve_unit_id_for_order_item(db, item)
        if action == "reserve":
            _apply_reserve(
                db,
                order=order,
                order_item=item,
                unit_id=unit_id,
                operator_user_id=operator_user_id,
                from_status=previous_status_code,
                to_status=new_status_code,
            )
        elif action == "commit_deduct":
            _apply_commit_deduct(
                db,
                order=order,
                order_item=item,
                unit_id=unit_id,
                operator_user_id=operator_user_id,
                from_status=previous_status_code,
                to_status=new_status_code,
            )
        elif action == "release":
            _apply_release(
                db,
                order=order,
                order_item=item,
                unit_id=unit_id,
                operator_user_id=operator_user_id,
                from_status=previous_status_code,
                to_status=new_status_code,
            )


def list_balances(
    db: Session,
    *,
    product_id: uuid.UUID | None = None,
    unit_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 200,
) -> list[InventoryBalanceResponse]:
    rows = crud.list_inventory_balances(db, product_id=product_id, unit_id=unit_id, skip=skip, limit=limit)
    return [_to_balance_response(row) for row in rows]


def list_ledger(
    db: Session,
    *,
    product_id: uuid.UUID | None = None,
    unit_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 200,
) -> list[InventoryLedgerResponse]:
    rows = crud.list_inventory_ledger(
        db,
        product_id=product_id,
        unit_id=unit_id,
        order_id=order_id,
        skip=skip,
        limit=limit,
    )
    return [_to_ledger_response(row) for row in rows]


def adjust_inventory_manually(
    db: Session,
    *,
    payload: InventoryManualAdjustRequest,
    operator_user_id: uuid.UUID,
) -> InventoryBalanceResponse:
    balance = crud.get_inventory_balance_for_update(db, payload.product_id, payload.unit_id)
    if balance is None:
        raise_error(
            ErrorCode.BAD_REQUEST,
            detail=f"Inventory balance not found for product_id={payload.product_id}, unit_id={payload.unit_id}",
        )

    new_actual = balance.actual_stock + payload.delta
    if new_actual < 0:
        raise_error(ErrorCode.CONFLICT, detail="Manual adjustment would make actual stock negative")
    if new_actual < balance.reserved_stock:
        raise_error(
            ErrorCode.CONFLICT,
            detail="Manual adjustment would make actual stock lower than reserved stock",
        )

    balance.actual_stock = new_actual
    balance.manual_adjustment_stock += payload.delta

    _write_ledger(
        db,
        balance=balance,
        action=InventoryLedgerAction.MANUAL_ADJUST,
        quantity=abs(payload.delta),
        delta_actual=payload.delta,
        delta_reserved=0,
        order_id=None,
        order_item_id=None,
        from_status=None,
        to_status=None,
        operator_user_id=operator_user_id,
        note=payload.note,
    )

    db.commit()
    db.refresh(balance)
    return _to_balance_response(balance)
