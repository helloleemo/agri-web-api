import uuid

from pydantic import BaseModel, ConfigDict, Field


class OrderStatusResponse(BaseModel):
    id: uuid.UUID
    code: int
    name: str
    customer_email_subject_template: str | None = None
    customer_email_body_template: str | None = None
    admin_email_subject_template: str | None = None
    admin_email_body_template: str | None = None


class OrderStatusEmailTemplateUpdate(BaseModel):
    customer_email_subject_template: str | None = Field(default=None, max_length=255)
    customer_email_body_template: str | None = None
    admin_email_subject_template: str | None = Field(default=None, max_length=255)
    admin_email_body_template: str | None = None

    model_config = ConfigDict(from_attributes=True)
