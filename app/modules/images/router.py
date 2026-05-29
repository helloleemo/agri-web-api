
from __future__ import annotations

import uuid
from typing import cast

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.common.response import created, deleted, ok
from app.modules.common.schema import ApiResponse
from app.modules.images import crud, service
from app.modules.images.schema import (
    ImageAssetResponse,
    ImageBindingCreate,
    ImageBindingResponse,
    ImageBindingUpdate,
    ImageCompleteRequest,
    ImageInitRequest,
    ImageInitResponse,
    ImageTargetType,
)

router = APIRouter(
    prefix="/images",
    tags=["Images"],
)


@router.post(
    "/init",
    response_model=ApiResponse[ImageInitResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def init_image_upload(payload: ImageInitRequest, db: Session = Depends(get_db)):
    asset_id = uuid.uuid4()
    storage_key = service.build_storage_key(asset_id=asset_id, filename=payload.filename)
    asset = crud.create_image_asset(
        db,
        asset_id=asset_id,
        storage_key=storage_key,
        url=service.build_public_url(storage_key),
        mime_type=payload.mime_type,
        size_bytes=payload.size_hint,
    )

    data = ImageInitResponse(
        image_asset_id=asset.id,
        storage_key=asset.storage_key,
        upload_url=service.build_upload_url(asset.id),
        expires_in=900,
    )
    return created(data, "image upload initialized")


@router.post(
    "/complete",
    response_model=ApiResponse[ImageAssetResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def complete_image_upload(payload: ImageCompleteRequest, db: Session = Depends(get_db)):
    asset = crud.get_image_asset_by_id(db, payload.image_asset_id)
    if asset is None:
        return ok(None, "image asset not found")
    return ok(service.to_image_asset_response(asset), "image upload completed")


@router.post(
    "/bindings",
    response_model=ApiResponse[ImageBindingResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def create_image_binding(payload: ImageBindingCreate, db: Session = Depends(get_db)):
    asset = crud.get_image_asset_by_id(db, payload.image_asset_id)
    if asset is None:
        return ok(None, "image asset not found")

    if payload.is_primary:
        crud.unset_primary_for_target(
            db,
            target_type=payload.target_type,
            target_id=payload.target_id,
        )

    binding = crud.create_image_binding(
        db,
        payload={
            "image_asset_id": payload.image_asset_id,
            "target_type": payload.target_type,
            "target_id": payload.target_id,
            "role": payload.role,
            "sort_order": payload.sort_order,
            "is_primary": payload.is_primary,
        },
    )
    created_binding = crud.get_binding_with_asset(db, binding.id)
    if created_binding is None:
        created_binding = binding
    return created(service.to_image_binding_response(created_binding), "image binding created")


@router.get(
    "",
    response_model=ApiResponse[list[ImageBindingResponse]],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def list_image_bindings(
    target_type: ImageTargetType = Query(...),
    target_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
):
    rows = crud.list_bindings_by_target(db, target_type=target_type, target_id=target_id)
    return ok([service.to_image_binding_response(row) for row in rows], "image bindings fetched")


@router.patch(
    "/bindings/{binding_id}",
    response_model=ApiResponse[ImageBindingResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def update_image_binding(
    binding_id: uuid.UUID,
    payload: ImageBindingUpdate,
    db: Session = Depends(get_db),
):
    binding = crud.get_binding_by_id(db, binding_id)
    if binding is None:
        return ok(None, "image binding not found")

    patch_data = payload.model_dump(exclude_unset=True)
    if patch_data.get("is_primary"):
        crud.unset_primary_for_target(
            db,
            target_type=cast(ImageTargetType, binding.target_type),
            target_id=binding.target_id,
            exclude_binding_id=binding.id,
        )

    crud.apply_binding_patch(db, binding, patch_data)
    updated = crud.get_binding_with_asset(db, binding.id)
    if updated is None:
        updated = binding
    return ok(service.to_image_binding_response(updated), "image binding updated")


@router.delete(
    "/bindings/{binding_id}",
    response_model=ApiResponse[dict[str, str]],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def delete_image_binding(binding_id: uuid.UUID, db: Session = Depends(get_db)):
    binding = crud.get_binding_by_id(db, binding_id)
    if binding is None:
        return ok(None, "image binding not found")

    crud.delete_binding(db, binding)
    return deleted(str(binding_id), "image binding deleted")