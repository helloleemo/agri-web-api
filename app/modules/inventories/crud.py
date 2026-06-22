from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.modules.inventories.model import InventoryBalance, InventoryLedger


def get_inventory_balance_for_update(db: Session, product_id: uuid.UUID, unit_id: uuid.UUID) -> InventoryBalance | None:
    stmt = (
        select(InventoryBalance)
        .where(InventoryBalance.product_id == product_id, InventoryBalance.unit_id == unit_id)
        .with_for_update()
    )
    return db.scalar(stmt)


def get_inventory_balance(db: Session, product_id: uuid.UUID, unit_id: uuid.UUID) -> InventoryBalance | None:
    stmt = select(InventoryBalance).where(InventoryBalance.product_id == product_id, InventoryBalance.unit_id == unit_id)
    return db.scalar(stmt)


def list_inventory_balances(
    db: Session,
    product_id: uuid.UUID | None = None,
    unit_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 200,
) -> list[InventoryBalance]:
    stmt: Select[tuple[InventoryBalance]] = select(InventoryBalance).options(
        joinedload(InventoryBalance.product),
        joinedload(InventoryBalance.unit),
    )
    if product_id is not None:
        stmt = stmt.where(InventoryBalance.product_id == product_id)
    if unit_id is not None:
        stmt = stmt.where(InventoryBalance.unit_id == unit_id)

    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def create_inventory_ledger(db: Session, payload: dict) -> InventoryLedger:
    entry = InventoryLedger(**payload)
    db.add(entry)
    db.flush()
    return entry


def list_inventory_ledger(
    db: Session,
    product_id: uuid.UUID | None = None,
    unit_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 200,
) -> list[InventoryLedger]:
    stmt: Select[tuple[InventoryLedger]] = select(InventoryLedger).options(
        joinedload(InventoryLedger.product),
        joinedload(InventoryLedger.unit),
    )
    if product_id is not None:
        stmt = stmt.where(InventoryLedger.product_id == product_id)
    if unit_id is not None:
        stmt = stmt.where(InventoryLedger.unit_id == unit_id)
    if order_id is not None:
        stmt = stmt.where(InventoryLedger.order_id == order_id)

    stmt = stmt.order_by(InventoryLedger.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())
