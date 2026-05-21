import uuid
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import ForeignKey, Index, String
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
        Index("idx_users_role_id", "role_id"),
        Index("idx_users_status_id", "status_id"),
    )

    # data table

    # user info
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
    )
    status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statuses.id"),
        nullable=False,
    )

    created_at: Mapped[str] = mapped_column(String(20), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(20), nullable=False)

    # relationships
    orders: Mapped[list["Order"]] = relationship(
        "Order", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

    status: Mapped["Status"] = relationship("Status")
    role: Mapped["Role"] = relationship("Role", back_populates="users")