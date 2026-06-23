from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SiteContentUpdate(BaseModel):
    content_data: dict[str, Any]


class SiteContentResponse(BaseModel):
    id: uuid.UUID
    page_key: str
    content_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PageAssetUploadResponse(BaseModel):
    bucket: str
    object_path: str
    public_url: str
