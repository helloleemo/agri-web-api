import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.products.model import Product
from app.modules.products.schema import ProductCreate, ProductUpdate

# 'create_product()
# get_product_by_id()
# get_products()
# update_product()
# delete_product()'

def get_product_by_id(db:Session, product_id:uuid.UUID) -> Product | None:
    stmt = select(Product).where(Product.id == product_id)
    return db.scalar(stmt)


def get_products(db: Session, skip: int = 0, limit: int = 10) -> list[Product]:
    stmt = select(Product).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

def create_product(db:Session, product_create:ProductCreate) -> Product:
    new_product = Product(**product_create.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update_product(db:Session, product_id:uuid.UUID, product_update:ProductUpdate) -> Product | None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    for field, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product

def delete_product(db:Session, product:Product) -> None:
    db.delete(product)
    db.commit()