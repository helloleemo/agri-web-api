import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.common.pagination import Pagination
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.products.model import Product, ProductUnits
from app.modules.products.schema import ProductCreate, ProductUpdate
from app.modules.statuses.constants import StatusCode
from app.modules.units.model import Unit

def _validate_units_payload(db: Session, units_payload: list[dict]) -> None:
    unit_ids = [item["unit_id"] for item in units_payload]
    if len(unit_ids) != len(set(unit_ids)):
        raise_error(ErrorCode.BAD_REQUEST, detail="Duplicate unit_id in product units payload")

    existing_ids = set(db.scalars(select(Unit.id).where(Unit.id.in_(unit_ids))).all())
    missing_ids = [str(unit_id) for unit_id in unit_ids if unit_id not in existing_ids]
    if missing_ids:
        raise_error(ErrorCode.BAD_REQUEST, detail=f"Invalid unit_id(s): {', '.join(missing_ids)}")


# 'create_product()
# get_product_by_id()
# get_products()
# update_product()
# delete_product()'

def get_product_by_id(db:Session, product_id:uuid.UUID) -> Product | None:
    stmt = (
        select(Product)
        .where(
            Product.id == product_id,
            Product.status_code != StatusCode.DELETED.value
        )
        .options(
            selectinload(Product.category), 
            selectinload(Product.images),
            selectinload(Product.product_units).selectinload(ProductUnits.unit),
        )
   ) 
    return db.scalar(stmt)


def get_products(db: Session, pagination: Pagination) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.status_code != StatusCode.DELETED.value)
        .options(selectinload(Product.product_units).selectinload(ProductUnits.unit))
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return list(db.scalars(stmt).all())

def create_product(db:Session, product_create:ProductCreate) -> Product:
    payload = product_create.model_dump(exclude={"units", "category_name", "images"})  # object轉換成可操作的dict
    units_payload = [unit.model_dump() for unit in product_create.units]
    _validate_units_payload(db, units_payload)

    new_product = Product(**payload) # **dict展開，會建立新物件

    db.add(new_product)
    db.flush()

    for item in units_payload:
        db.add(ProductUnits(product_id=new_product.id, **item))

    db.commit()
    return get_product_by_id(db, new_product.id) or new_product


def update_product(db:Session, product_id:uuid.UUID, product_update:ProductUpdate) -> Product | None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    payload = product_update.model_dump(exclude_unset=True, exclude={"category_name", "images"}) # 只保留有的欄位(部分更新 且沒有的欄位不會被覆蓋)
    units_payload = payload.pop("units", None)

    for field, value in payload.items(): # 改「已存在的物件」
        setattr(product, field, value)

    if units_payload is not None:
        _validate_units_payload(db, units_payload)
        product.product_units.clear()
        db.flush()
        for item in units_payload:
            product.product_units.append(ProductUnits(**item))

    db.commit() # 寫進資料庫
    return get_product_by_id(db, product.id) or product

def delete_product(db:Session, product_id:uuid.UUID) -> None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    product.status_code = StatusCode.DELETED.value
    db.commit()