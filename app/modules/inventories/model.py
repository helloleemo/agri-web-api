from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.modules.orders.model import Order, OrderItem
    from app.modules.products.model import Product
    from app.modules.units.model import Unit
    from app.modules.users.model import User


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("product_id", "unit_id", name="uq_inventory_balances_product_unit"),
        CheckConstraint("initial_stock >= 0", name="ck_inventory_balances_initial_non_negative"),
        CheckConstraint("actual_stock >= 0", name="ck_inventory_balances_actual_non_negative"),
        CheckConstraint("reserved_stock >= 0", name="ck_inventory_balances_reserved_non_negative"),
        CheckConstraint("actual_stock >= reserved_stock", name="ck_inventory_balances_actual_gte_reserved"),
        Index("idx_inventory_balances_product_id", "product_id"),
        Index("idx_inventory_balances_unit_id", "unit_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)

    initial_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manual_adjustment_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    product: Mapped["Product"] = relationship("Product")
    unit: Mapped["Unit"] = relationship("Unit")


class InventoryLedger(Base):
    __tablename__ = "inventory_ledger"
    __table_args__ = (
        Index("idx_inventory_ledger_product_unit", "product_id", "unit_id"),
        Index("idx_inventory_ledger_order_item", "order_item_id"),
        Index("idx_inventory_ledger_created_at", "created_at"),
        Index("idx_inventory_ledger_operator_user_id", "operator_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    order_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("order_items.id"), nullable=True)

    action: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    actual_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    from_order_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    to_order_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    operator_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    product: Mapped["Product"] = relationship("Product")
    unit: Mapped["Unit"] = relationship("Unit")
    order: Mapped["Order | None"] = relationship("Order")
    order_item: Mapped["OrderItem | None"] = relationship("OrderItem")
    operator: Mapped["User | None"] = relationship("User")
