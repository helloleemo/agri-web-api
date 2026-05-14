
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    email: str = Field(..., max_length=120)
    user_name: str = Field(..., max_length=20)
    role_id: uuid.UUID

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=200)

class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=120)
    user_name: str | None = Field(default=None, max_length=20)
    password: str | None = Field(default=None, min_length=8, max_length=200)
    role_id: uuid.UUID | None = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    user_name: str
    role_id: uuid.UUID
    status_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
