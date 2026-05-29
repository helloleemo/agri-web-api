
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ImageAsset(Base):
    __tablename__ = "image_assets"

    __table_args__ = (
        Index("idx_image_assets_storage_key", "storage_key"),
        CheckConstraint("size_bytes >= 0", name="ck_image_assets_size_non_negative"),
        CheckConstraint("width >= 1", name="ck_image_assets_width_positive"),
        CheckConstraint("height >= 1", name="ck_image_assets_height_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(300), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    base64_data: Mapped[str | None] = mapped_column(String(1000), nullable=True)  
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
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

    bindings: Mapped[list[ImageBinding]] = relationship(
        "ImageBinding",
        back_populates="image_asset",
        cascade="all, delete-orphan",
    )


class ImageBinding(Base):
    __tablename__ = "image_bindings"

    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_image_bindings_sort_order_non_negative"),
        CheckConstraint(
            "target_type IN ('product', 'user', 'page')",
            name="ck_image_bindings_target_type_allowed",
        ),
        Index("idx_image_bindings_image_asset_id", "image_asset_id"),
        Index("idx_image_bindings_target", "target_type", "target_id"),
        Index(
            "uq_image_bindings_primary_per_target",
            "target_type",
            "target_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("image_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
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

    image_asset: Mapped[ImageAsset] = relationship("ImageAsset", back_populates="bindings")

