from datetime import datetime
import uuid
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.orders.model import Order
    from app.modules.roles.model import Role
    from app.modules.statuses.model import Status


class User(Base):

    __tablename__ = "users"

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_role_code", "role_code"),
        Index("idx_users_status_code", "status_code"),
    )

    # data table

    # user info
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    # Foreign keys
    status_code:Mapped[int] = mapped_column(Integer,ForeignKey("statuses.code"),nullable=False)
    role_code:Mapped[int] = mapped_column(Integer,ForeignKey("roles.code"),nullable=False)


    # relationships
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan"
    )
