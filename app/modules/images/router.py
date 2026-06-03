
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.common.errors import raise_not_found_image
from app.modules.common.messages import ImageMessages
from app.modules.common.schema import ApiResponse
from app.modules.common.response import created, deleted, ok
from app.modules.images.schema import ImageResponse, ImageUpdate

from app.modules.images import service


router = APIRouter(
    prefix="/images",
    tags=["Images"],
)

@router.get("/{product_id}", response_model=ApiResponse[list[ImageResponse]], status_code=status.HTTP_200_OK)
def list_images(
    product_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    images = service.list_images(db, product_id)
    return ok(images, ImageMessages.LIST)


@router.post("", response_model=ApiResponse[ImageResponse], status_code=status.HTTP_201_CREATED)
def create_image(
    product_id: uuid.UUID = Form(...),
    is_primary: bool = Form(False),
    sort_order: int = Form(0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    created_image = service.create_image(
        db=db,
        product_id=product_id,
        file=file,
        is_primary=is_primary,
        sort_order=sort_order,
    )
    return created(created_image, ImageMessages.CREATE)

@router.put("/{image_id}", response_model=ApiResponse[ImageResponse], status_code=status.HTTP_200_OK)
def update_image(
    image_id: uuid.UUID,
    image_update: ImageUpdate,
    db: Session = Depends(get_db)
):
    updated_image = service.update_image(db, image_id, image_update)
    if not updated_image:
        return raise_not_found_image(str(image_id))
    return ok(updated_image, ImageMessages.UPDATE)


@router.delete("/{image_id}", response_model=ApiResponse[dict[str, str]], status_code=status.HTTP_200_OK)
def delete_image(
    image_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    deleted_image = service.delete_image(db, image_id)
    if not deleted_image:
        return raise_not_found_image(str(image_id))
    return deleted(str(image_id), ImageMessages.DELETE)