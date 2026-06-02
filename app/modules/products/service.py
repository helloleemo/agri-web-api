import uuid
from sqlalchemy.orm import Session

from app.modules.products import crud
from app.modules.products.model import Product
from app.modules.products.schema import ProductCreate, ProductResponse, ProductUpdate
from app.modules.statuses.constants import StatusCode


def _to_product_response(db: Session, product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        category=product.category,
        origin=product.origin,
        unit=product.unit,
        price=product.price,
        stock=product.stock,
        description=product.description,
        image=product.image,
        image_group=product.image_group,
        status_code=StatusCode(product.status_code),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )

def create_product(db: Session, data: ProductCreate) -> ProductResponse:
    product = crud.create_product(db, data)
    return _to_product_response(db, product)


def get_product(db: Session, product_id: uuid.UUID) -> ProductResponse | None:
    product = crud.get_product_by_id(db, product_id)
    if not product:
        return None
    return _to_product_response(db, product)


def list_products(db: Session, skip: int = 0, limit: int = 10) -> list[ProductResponse]:
    products = crud.get_products(db, skip=skip, limit=limit)
    return [_to_product_response(db, product) for product in products]


def update_product(
    db: Session,
    product_id: uuid.UUID,
    data: ProductUpdate,
) -> ProductResponse | None:
    updated = crud.update_product(db, product_id, data)
    if updated is None:
        return None
    return _to_product_response(db, updated)


def delete_product(db: Session, product_id: uuid.UUID) -> bool:
    product = crud.get_product_by_id(db, product_id)
    if product is None:
        return False
    crud.delete_product(db, product_id)
    return True