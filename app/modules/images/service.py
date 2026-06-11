import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.modules.images import crud
from app.modules.images.model import Image
from app.modules.images.schema import ImageCreate, ImageResponse, ImageUpdate


UPLOAD_ROOT = Path("uploads") / "images"
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


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


def _save_upload_file(file_path: Path, file: UploadFile) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


def list_images(db: Session, product_id: uuid.UUID) -> list[ImageResponse]:
    images = crud.get_images_by_product_id(db, product_id)
    return [_to_image_response(image) for image in images]


def create_image(
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

    stored_filename = f"{uuid.uuid4()}{suffix}"
    file_path = UPLOAD_ROOT / str(product_id) / stored_filename
    _save_upload_file(file_path, file)

    image_create = ImageCreate(
        product_id=product_id,
        is_primary=is_primary,
        sort_order=sort_order,
    )
    image = crud.create_image(
        db=db,
        image_create=image_create,
        stored_filename=stored_filename,
        file_url=_build_file_url(product_id, stored_filename),
    )
    return _to_image_response(image)


def create_images_batch(
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

    return [
        create_image(
            db=db,
            product_id=product_id,
            file=file,
            is_primary=(primary_index == index),
            sort_order=sort_order_start + index,
        )
        for index, file in enumerate(files)
    ]


def update_image(db: Session, image_id: uuid.UUID, image_update: ImageUpdate) -> ImageResponse | None:
    image = crud.update_image(db, image_id, image_update)
    if not image:
        return None
    return _to_image_response(image)


def delete_image(db: Session, image_id: uuid.UUID) -> bool:
    image = crud.get_image_by_id(db, image_id)
    if not image:
        return False

    file_path = Path.cwd() / image.file_url.lstrip("/")
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass

    return crud.delete_image_by_id(db, image_id)
