import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.modules.roles.constants import RoleCode
from app.modules.statuses.constants import StatusCode


class UserBase(BaseModel):
    email: str = Field(..., max_length=120) # ...是必填
    user_name: str = Field(..., max_length=20)

class UserCreate(UserBase):
    role_code: RoleCode = Field(default=RoleCode.ROLE_MEMBER)
    password: str = Field(..., min_length=8, max_length=200)

class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=120)
    user_name: str | None = Field(default=None, max_length=20)
    password: str | None = Field(default=None, min_length=8, max_length=200)
    role_code: RoleCode | None = Field(default=None)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=200)
    new_password: str = Field(..., min_length=8, max_length=200)

class UserOrderItemResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str | None = None
    quantity: int


class UserOrderResponse(BaseModel):
    order_id: uuid.UUID
    order_no: str | None = None
    items: list[UserOrderItemResponse] = Field(default_factory=list)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    user_name: str
    role_code: RoleCode
    status_code: StatusCode
    email_verified_at: datetime | None = None
    orders: list[UserOrderResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)