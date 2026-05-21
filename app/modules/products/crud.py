import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.products.model import Product
from app.modules.products.schema import ProductCreate, ProductUpdate
from app.modules.statuses.constants import STATUS_CODE_DELETED, STATUS_CODE_ENABLED
from app.modules.statuses.utils import get_status_id_by_code

# 'create_product()
# get_product_by_id()
# get_products()
# update_product()
# delete_product()'

def get_product_by_id(db:Session, product_id:uuid.UUID) -> Product | None:
    deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
    conditions = [Product.id == product_id]
    if deleted_status_id is not None:
        conditions.append(Product.status_id != deleted_status_id)

    stmt = select(Product).where(*conditions)
    return db.scalar(stmt)


def get_products(db: Session, skip: int = 0, limit: int = 10) -> list[Product]:
    deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
    conditions = []
    if deleted_status_id is not None:
        conditions.append(Product.status_id != deleted_status_id)

    stmt = select(Product).where(*conditions).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

def create_product(db:Session, product_create:ProductCreate) -> Product:
    payload = product_create.model_dump()
    status_code = payload.pop("status_id", STATUS_CODE_ENABLED)
    status_id = get_status_id_by_code(db, status_code)
    if status_id is None:
        raise ValueError(f"Status code {status_code} is not configured")
    payload["status_id"] = status_id

    new_product = Product(**payload)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update_product(db:Session, product_id:uuid.UUID, product_update:ProductUpdate) -> Product | None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    payload = product_update.model_dump(exclude_unset=True)
    if "status_id" in payload:
        status_id = get_status_id_by_code(db, payload["status_id"])
        if status_id is None:
            raise ValueError(f"Status code {payload['status_id']} is not configured")
        payload["status_id"] = status_id

    for field, value in payload.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product

def delete_product(db:Session, product:Product) -> None:
    deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
    if deleted_status_id is None:
        raise ValueError("Deleted status is not configured")

    product.status_id = deleted_status_id
    db.commit()