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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


if TYPE_CHECKING:
    from app.modules.orders.model import OrderItem
    from app.modules.categories.model import Category
    from app.modules.images.model import Image
    from app.modules.units.model import Unit

class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        Index("idx_products_name", "name"),
        Index("idx_products_category_id", "category_id"),
        Index("idx_products_status_code", "status_code"),
        Index("idx_products_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # category: Mapped[str] = mapped_column(String(60), nullable=False, default="other")
    origin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # image:Mapped[str | None] = mapped_column(String(300), nullable=True)
    # image_group:Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    # Foreign keys
    status_code:Mapped[int] = mapped_column(Integer,ForeignKey("statuses.code"),nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)

    # relationships
    product_units: Mapped[list["ProductUnits"]] = relationship(
        "ProductUnits",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    units: Mapped[list["Unit"]] = relationship(
        "Unit",
        secondary="product_units",
        back_populates="products",
        viewonly=True,
    )
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    images: Mapped[list["Image"]] = relationship("Image", back_populates="product", cascade="all, delete-orphan")



class ProductUnits(Base):
    __tablename__ = "product_units"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id"), primary_key=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped["Product"] = relationship("Product", back_populates="product_units")
    unit: Mapped["Unit"] = relationship("Unit", back_populates="product_units")