from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.images.model import ImageAsset, ImageBinding
from app.modules.images.schema import ImageTargetType


def create_image_asset(
	db: Session,
	*,
	asset_id: uuid.UUID,
	storage_key: str,
	url: str,
	mime_type: str,
	size_bytes: int | None,
) -> ImageAsset:
	asset = ImageAsset(
		id=asset_id,
		storage_key=storage_key,
		url=url,
		mime_type=mime_type,
		size_bytes=size_bytes,
	)
	db.add(asset)
	db.commit()
	db.refresh(asset)
	return asset


def get_image_asset_by_id(db: Session, image_asset_id: uuid.UUID) -> ImageAsset | None:
	return db.get(ImageAsset, image_asset_id)


def create_image_binding(db: Session, payload: dict) -> ImageBinding:
	binding = ImageBinding(**payload)
	db.add(binding)
	db.commit()
	db.refresh(binding)
	return binding


def unset_primary_for_target(
	db: Session,
	*,
	target_type: ImageTargetType,
	target_id: uuid.UUID,
	exclude_binding_id: uuid.UUID | None = None,
) -> None:
	stmt = select(ImageBinding).where(
		ImageBinding.target_type == target_type,
		ImageBinding.target_id == target_id,
		ImageBinding.is_primary.is_(True),
	)
	if exclude_binding_id is not None:
		stmt = stmt.where(ImageBinding.id != exclude_binding_id)

	for existing in db.scalars(stmt):
		existing.is_primary = False
	db.flush()


def get_binding_with_asset(db: Session, binding_id: uuid.UUID) -> ImageBinding | None:
	stmt = (
		select(ImageBinding)
		.options(joinedload(ImageBinding.image_asset))
		.where(ImageBinding.id == binding_id)
	)
	return db.scalar(stmt)


def get_binding_by_id(db: Session, binding_id: uuid.UUID) -> ImageBinding | None:
	return db.get(ImageBinding, binding_id)


def list_bindings_by_target(
	db: Session,
	*,
	target_type: ImageTargetType,
	target_id: uuid.UUID,
) -> list[ImageBinding]:
	stmt = (
		select(ImageBinding)
		.options(joinedload(ImageBinding.image_asset))
		.where(
			ImageBinding.target_type == target_type,
			ImageBinding.target_id == target_id,
		)
		.order_by(ImageBinding.sort_order.asc(), ImageBinding.created_at.asc())
	)
	return list(db.scalars(stmt).all())


def apply_binding_patch(db: Session, binding: ImageBinding, patch_data: dict) -> None:
	for field, value in patch_data.items():
		setattr(binding, field, value)
	db.commit()


def delete_binding(db: Session, binding: ImageBinding) -> None:
	db.delete(binding)
	db.commit()
