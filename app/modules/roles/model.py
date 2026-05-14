

from datetime import datetime
import uuid
from app.modules.users.model import User
from app.db.base import Base
from sqlalchemy import UUID, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # relationships
    from sqlalchemy.orm import Mapped, relationship

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
    )