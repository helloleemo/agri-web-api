import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrderStatus(Base):
    __tablename__ = "order_statuses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_email_subject_template: Mapped[str] = mapped_column(String(255), nullable=True)
    customer_email_body_template: Mapped[str] = mapped_column(Text, nullable=True)
    admin_email_subject_template: Mapped[str] = mapped_column(String(255), nullable=True)
    admin_email_body_template: Mapped[str] = mapped_column(Text, nullable=True)
