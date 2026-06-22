from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = (
        CheckConstraint("discount_value >= 0", name="ck_coupons_discount_value_non_negative"),
        CheckConstraint("used_count >= 0", name="ck_coupons_used_count_non_negative"),
        Index("idx_coupons_code", "code"),
        Index("idx_coupons_status_code", "status_code"),
        Index("idx_coupons_starts_at", "starts_at"),
        Index("idx_coupons_ends_at", "ends_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    discount_type: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    min_order_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_discount_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status_code: Mapped[int] = mapped_column(Integer, ForeignKey("statuses.code"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
