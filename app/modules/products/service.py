import uuid
from sqlalchemy.orm import Session

from app.modules.products import crud
from app.modules.products.model import Product
from app.modules.products.schema import ProductCreate, ProductUpdate

def create_product(db: Session, data: ProductCreate) -> Product:
    return crud.create_product(db, data)


def get_product(db: Session, product_id: uuid.UUID) -> Product | None:
    return crud.get_product_by_id(db, product_id)


def list_products(db: Session, skip: int = 0, limit: int = 10) -> list[Product]:
    return crud.get_products(db, skip=skip, limit=limit)


def update_product(
    db: Session,
    product_id: uuid.UUID,
    data: ProductUpdate,
) -> Product | None:
    product = crud.get_product_by_id(db, product_id)
    if product is None:
        return None
    return crud.update_product(db, product_id, data)


def delete_product(db: Session, product_id: uuid.UUID) -> bool:
    product = crud.get_product_by_id(db, product_id)
    if product is None:
        return False
    crud.delete_product(db, product)
    return True