from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.db.base import Base
from app.modules.statuses.model import Status


if TYPE_CHECKING:
    from app.modules.orders.model import OrderItem


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        Index("idx_products_name", "name"),
        Index("idx_products_category", "category"),
        Index("idx_products_status_id", "status_id"),
        Index("idx_products_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="other")
    origin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image:Mapped[str | None] = mapped_column(String(300), nullable=True)
    image_group:Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("statuses.id"), nullable=False)
    status: Mapped["Status"] = relationship("Status")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )