from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
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

class Category(Base):
    __tablename__="categories"
    # __table_args__=()

    id : Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name : Mapped[str]=mapped_column(String(60), nullable=False, unique=True)

    created_at : Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at : Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())