from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
import app.modules.products.model  # noqa: F401
import app.modules.units.model  # noqa: F401
import app.modules.categories.model  # noqa: F401
import app.modules.images.model  # noqa: F401

if TYPE_CHECKING:
    from app.modules.products.model import Product
    from app.modules.order_statuses.model import OrderStatus
    from app.modules.statuses.model import Status
    from app.modules.users.model import User




class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_customer_email", "customer_email"),
        Index("idx_orders_status_code", "status_code"),
        Index("idx_orders_order_status_code", "order_status_code"),
        Index("idx_orders_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    customer_email: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    # Foreign keys
    status_code: Mapped[int] = mapped_column(Integer, ForeignKey("statuses.code"), nullable=False)
    order_status_code: Mapped[int] = mapped_column(Integer, ForeignKey("order_statuses.code"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    order_status: Mapped["OrderStatus"] = relationship("OrderStatus")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem",back_populates="order",cascade="all, delete-orphan")
    

class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ch_order_items_quantity_positive"),
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_product_id", "product_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Foreign keys
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")


