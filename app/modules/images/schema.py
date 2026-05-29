from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ImageTargetType = Literal["product", "user", "page"]
ImageStatus = Literal["temp", "active", "deleted", "failed"]


class ImageInitRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., min_length=1, max_length=120)
    size_hint: int | None = Field(default=None, ge=0)


class ImageInitResponse(BaseModel):
    image_asset_id: uuid.UUID
    storage_key: str
    upload_url: str
    expires_in: int = Field(..., ge=1)


class ImageCompleteRequest(BaseModel):
    image_asset_id: uuid.UUID


class ImageAssetBase(BaseModel):
    id: uuid.UUID
    url: str
    storage_key: str
    mime_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    status: ImageStatus = "active"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageAssetResponse(ImageAssetBase):
    display_url: str | None = None


class ImageBindingCreate(BaseModel):
    image_asset_id: uuid.UUID
    target_type: ImageTargetType
    target_id: uuid.UUID
    role: str | None = Field(default=None, max_length=50)
    sort_order: int = Field(default=0, ge=0)
    is_primary: bool = False


class ImageBindingUpdate(BaseModel):
    role: str | None = Field(default=None, max_length=50)
    sort_order: int | None = Field(default=None, ge=0)
    is_primary: bool | None = None


class ImageBindingResponse(BaseModel):
    id: uuid.UUID
    image_asset_id: uuid.UUID
    target_type: ImageTargetType
    target_id: uuid.UUID
    role: str | None = None
    sort_order: int
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    image: ImageAssetResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ImageListQuery(BaseModel):
    target_type: ImageTargetType
    target_id: uuid.UUID