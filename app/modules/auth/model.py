import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuthEmailTemplate(Base):
    __tablename__ = "auth_email_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_type: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    # template_type values:
    # 1 = REGISTRATION_VERIFICATION
    # 2 = PASSWORD_RESET
    subject_template: Mapped[str] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=True)
