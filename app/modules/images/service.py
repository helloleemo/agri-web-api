import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image as PILImage
from PIL import ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.modules.images import crud
from app.modules.images.model import Image
from app.modules.images.schema import ImageCreate, ImageResponse, ImageUpdate
import os
from app.core.supabase import supabase_client
# UPLOAD_ROOT = Path("uploads") / "images"
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
OUTPUT_IMAGE_SUFFIX = ".webp"
WEBP_QUALITY = 85


def _to_image_response(image: Image) -> ImageResponse:
    return ImageResponse(
        id=image.id,
        stored_filename=image.stored_filename,
        file_url=image.file_url,
        is_primary=image.is_primary,
        sort_order=image.sort_order,
        product_id=image.product_id,
        created_at=image.created_at,
    )


def _build_file_url(product_id: uuid.UUID, stored_filename: str) -> str:
    return f"/uploads/images/{product_id}/{stored_filename}"


# def _save_upload_file_as_webp(file_path: Path, file: UploadFile) -> None:
#     file_path.parent.mkdir(parents=True, exist_ok=True)
#     try:
#         with PILImage.open(file.file) as image:
#             image = ImageOps.exif_transpose(image)
#             if image.mode not in {"RGB", "RGBA"}:
#                 image = image.convert("RGBA")
#             image.save(file_path, format="WEBP", quality=WEBP_QUALITY, method=6)
#     except (UnidentifiedImageError, OSError):
#         raise HTTPException(status_code=400, detail="invalid image file")

async def _upload_to_supabase(
    product_id: uuid.UUID,
    file: UploadFile,
    stored_filename: str,
):
    contents = await file.read()

    try:
        with PILImage.open(io.BytesIO(contents)) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in {"RGB", "RGBA"}:
                img = img.convert("RGBA")
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=6)
            buffer.seek(0)
            webp_contents = buffer.read()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="invalid image file")

    object_path = f"products/{product_id}/{stored_filename}"

    supabase_client.storage.from_("products").upload(  # type: ignore[union-attr]
        path=object_path,
        file=webp_contents,
        file_options={
            "content-type": "image/webp",
            "upsert": "false",
        },
    )

    return (
        f"{os.getenv('SUPABASE_URL')}"
        f"/storage/v1/object/public/"
        f"products/{object_path}"
    )

def list_images(db: Session, product_id: uuid.UUID) -> list[ImageResponse]:
    images = crud.get_images_by_product_id(db, product_id)
    return [_to_image_response(image) for image in images]


async def create_image(
    db: Session,
    product_id: uuid.UUID,
    file: UploadFile,
    is_primary: bool = False,
    sort_order: int = 0,
) -> ImageResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="file name is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise HTTPException(status_code=400, detail="unsupported image file type")

    stored_filename = f"{uuid.uuid4()}.webp"

    file_url = await _upload_to_supabase(
        product_id,
        file,
        stored_filename,
    )

    existing_images = crud.get_images_by_product_id(db, product_id)
    should_be_primary = is_primary or not existing_images

    image_create = ImageCreate(
        product_id=product_id,
        is_primary=should_be_primary,
        sort_order=sort_order,
    )

    if should_be_primary:
        crud.clear_primary_by_product_id(db, product_id)

    image = crud.create_image(
        db=db,
        image_create=image_create,
        stored_filename=stored_filename,
        # file_url=_build_file_url(product_id, stored_filename),
        file_url=file_url,
    )
    return _to_image_response(image)


async def create_images_batch(
    db: Session,
    product_id: uuid.UUID,
    files: list[UploadFile],
    primary_index: int | None = None,
    sort_order_start: int = 0,
) -> list[ImageResponse]:
    if not files:
        raise HTTPException(status_code=400, detail="at least one file is required")

    if primary_index is not None and (primary_index < 0 or primary_index >= len(files)):
        raise HTTPException(status_code=400, detail="primary_index is out of range")

    if sort_order_start < 0:
        raise HTTPException(status_code=400, detail="sort_order_start must be non-negative")

    existing_images = crud.get_images_by_product_id(db, product_id)
    effective_primary_index = primary_index
    if effective_primary_index is None and not existing_images:
        effective_primary_index = 0

    results = []
    for index, file in enumerate(files):
        result = await create_image(
            db=db,
            product_id=product_id,
            file=file,
            is_primary=(effective_primary_index == index),
            sort_order=sort_order_start + index,
        )
        results.append(result)
    return results


def update_image(db: Session, image_id: uuid.UUID, image_update: ImageUpdate) -> ImageResponse | None:
    if image_update.is_primary is True:
        image = crud.get_image_by_id(db, image_id)
        if not image:
            return None
        crud.clear_primary_by_product_id(db, image.product_id, exclude_image_id=image_id)

    image = crud.update_image(db, image_id, image_update)
    if not image:
        return None
    return _to_image_response(image)


def delete_image(db: Session, image_id: uuid.UUID) -> bool:
    image = crud.get_image_by_id(db, image_id)
    if not image:
        return False

    try:
        object_path = (
            f"products/"
            f"{image.product_id}/"
            f"{image.stored_filename}"
        )
        supabase_client.storage.from_("products").remove([object_path])  # type: ignore[union-attr]
    except Exception:
        pass

    return crud.delete_image_by_id(db, image_id)
