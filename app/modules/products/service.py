import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.images.schema import ImageResponse
from app.modules.products import crud
from app.modules.inventories.model import InventoryBalance
from app.modules.products.model import Product
from app.modules.products.schema import ProductCreate, ProductResponse, ProductUnitResponse, ProductUpdate
from app.modules.statuses.constants import StatusCode


def _to_product_response(db: Session, product: Product) -> ProductResponse:
    units: list[ProductUnitResponse] = []
    for product_unit in product.product_units:
        available_stock = db.scalar(
            select(InventoryBalance.actual_stock - InventoryBalance.reserved_stock).where(
                InventoryBalance.product_id == product.id,
                InventoryBalance.unit_id == product_unit.unit_id,
            )
        )
        units.append(
            ProductUnitResponse(
                unit_id=product_unit.unit_id,
                unit_name=product_unit.unit.name if product_unit.unit else None,
                price=product_unit.price,
                stock=available_stock if available_stock is not None else product_unit.stock,
            )
        )

    units = sorted(units, key=lambda item: (item.unit_name or "", str(item.unit_id)))

    return ProductResponse(
        id=product.id,
        name=product.name,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        origin=product.origin,
        description=product.description,
        units=units,
        # image=product.image,
        # image_group=product.image_group,
        images=[ImageResponse(
            id=image.id,
            stored_filename=image.stored_filename,
            file_url=image.file_url,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
            product_id=image.product_id,
            created_at=image.created_at
        ) for image in product.images],
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


def list_products(db: Session) -> "list[ProductResponse]":
    products = crud.get_products(db)
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