
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.images.model import Image
from app.modules.images.schema import ImageCreate, ImageUpdate


def get_image_by_id(db: Session, image_id: uuid.UUID) -> Image | None:
    stmt = select(Image).where(Image.id == image_id)
    return db.scalar(stmt)


def get_images_by_product_id(db: Session, product_id: uuid.UUID) -> list[Image]:
    stmt = (
        select(Image)
        .where(Image.product_id == product_id)
        .order_by(Image.sort_order.asc(), Image.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def create_image(
    db: Session,
    image_create: ImageCreate,
    stored_filename: str,
    file_url: str,
) -> Image:
    payload = image_create.model_dump()
    new_image = Image(
        **payload,
        stored_filename=stored_filename,
        file_url=file_url,
    )

    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


def clear_primary_by_product_id(
    db: Session,
    product_id: uuid.UUID,
    exclude_image_id: uuid.UUID | None = None,
) -> None:
    stmt = update(Image).where(Image.product_id == product_id, Image.is_primary.is_(True))
    if exclude_image_id:
        stmt = stmt.where(Image.id != exclude_image_id)

    db.execute(stmt.values(is_primary=False))


def update_image(db: Session, image_id: uuid.UUID, image_update: ImageUpdate) -> Image | None:
    image = get_image_by_id(db, image_id)
    if not image:
        return None

    payload = image_update.model_dump(exclude_unset=True)

    for field, value in payload.items():
        setattr(image, field, value)

    db.commit()
    db.refresh(image)
    return image


def delete_image_by_id(db: Session, image_id: uuid.UUID) -> bool:
    image = get_image_by_id(db, image_id)
    if not image:
        return False

    db.delete(image)
    db.commit()
    return True
