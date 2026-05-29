from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from typing import cast
from urllib.parse import quote

from app.modules.images.model import ImageAsset, ImageBinding
from app.modules.images.schema import ImageAssetResponse, ImageBindingResponse, ImageTargetType

CDN_BASE_URL = os.getenv("CDN_BASE_URL", "http://localhost:8000/assets").rstrip("/")
SIGNED_URL_SECRET = os.getenv("SIGNED_URL_SECRET", "dev-secret")


def sanitize_filename(filename: str) -> str:
	return filename.strip().replace(" ", "_")


def build_storage_key(asset_id: uuid.UUID, filename: str) -> str:
	safe_name = quote(sanitize_filename(filename), safe="._-")
	return f"uploads/{asset_id}/{safe_name}"


def build_public_url(storage_key: str) -> str:
	return f"{CDN_BASE_URL}/{storage_key}"


def build_signed_url(storage_key: str, expires_in: int = 900) -> str:
	expires_at = int(time.time()) + expires_in
	payload = f"{storage_key}:{expires_at}".encode("utf-8")
	signature = hmac.new(SIGNED_URL_SECRET.encode("utf-8"), payload, hashlib.sha256).digest()
	token = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
	return f"{build_public_url(storage_key)}?exp={expires_at}&sig={token}"


def build_display_url(storage_key: str, private: bool = False, expires_in: int = 900) -> str:
	if private:
		return build_signed_url(storage_key=storage_key, expires_in=expires_in)
	return build_public_url(storage_key)


def build_upload_url(asset_id: uuid.UUID) -> str:
	return f"/images/upload/{asset_id}"


def to_image_asset_response(asset: ImageAsset, private: bool = False) -> ImageAssetResponse:
	return ImageAssetResponse(
		id=asset.id,
		url=asset.url,
		storage_key=asset.storage_key,
		mime_type=asset.mime_type,
		size_bytes=asset.size_bytes,
		width=asset.width,
		height=asset.height,
		status="active",
		created_at=asset.created_at,
		updated_at=asset.updated_at,
		display_url=build_display_url(asset.storage_key, private=private),
	)


def to_image_binding_response(binding: ImageBinding, private: bool = False) -> ImageBindingResponse:
	image = to_image_asset_response(binding.image_asset, private=private) if binding.image_asset else None
	return ImageBindingResponse(
		id=binding.id,
		image_asset_id=binding.image_asset_id,
		target_type=cast(ImageTargetType, binding.target_type),
		target_id=binding.target_id,
		role=binding.role,
		sort_order=binding.sort_order,
		is_primary=binding.is_primary,
		created_at=binding.created_at,
		updated_at=binding.updated_at,
		image=image,
	)
