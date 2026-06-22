import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.common.pagination import Pagination
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.categories.model import Category
from app.modules.inventories.constants import InventoryLedgerAction
from app.modules.inventories.model import InventoryBalance, InventoryLedger
from app.modules.products.model import Product, ProductUnits
from app.modules.products.schema import ProductCreate, ProductUpdate
from app.modules.statuses.constants import StatusCode
from app.modules.units.model import Unit


def _normalize_status_code(value: object) -> int | object:
    if isinstance(value, StatusCode):
        return value.value

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return value

        if normalized.isdigit():
            return int(normalized)

        try:
            return StatusCode[normalized].value
        except KeyError:
            return value

    return value

def _validate_units_payload(db: Session, units_payload: list[dict]) -> None:
    unit_ids = [item["unit_id"] for item in units_payload]
    if len(unit_ids) != len(set(unit_ids)):
        raise_error(ErrorCode.BAD_REQUEST, detail="Duplicate unit_id in product units payload")

    existing_ids = set(db.scalars(select(Unit.id).where(Unit.id.in_(unit_ids))).all())
    missing_ids = [str(unit_id) for unit_id in unit_ids if unit_id not in existing_ids]
    if missing_ids:
        raise_error(ErrorCode.BAD_REQUEST, detail=f"Invalid unit_id(s): {', '.join(missing_ids)}")


def _validate_category_id(db: Session, category_id: uuid.UUID) -> None:
    exists = db.scalar(select(Category.id).where(Category.id == category_id))
    if exists is None:
        raise_error(ErrorCode.BAD_REQUEST, detail=f"Invalid category_id: {category_id}")


def _ensure_inventory_balance_for_unit(
    db: Session,
    *,
    product_id: uuid.UUID,
    unit_id: uuid.UUID,
    initial_stock: int,
) -> None:
    existing_balance = db.scalar(
        select(InventoryBalance).where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.unit_id == unit_id,
        )
    )
    if existing_balance is not None:
        return

    new_balance = InventoryBalance(
        product_id=product_id,
        unit_id=unit_id,
        initial_stock=max(0, initial_stock),
        actual_stock=max(0, initial_stock),
        reserved_stock=0,
        manual_adjustment_stock=0,
    )
    db.add(new_balance)
    db.flush()

    if initial_stock > 0:
        db.add(
            InventoryLedger(
                product_id=product_id,
                unit_id=unit_id,
                order_id=None,
                order_item_id=None,
                action=InventoryLedgerAction.INITIALIZE.value,
                quantity=initial_stock,
                delta_actual=initial_stock,
                delta_reserved=0,
                actual_after=new_balance.actual_stock,
                reserved_after=new_balance.reserved_stock,
                available_after=new_balance.actual_stock - new_balance.reserved_stock,
                from_order_status_code=None,
                to_order_status_code=None,
                operator_user_id=None,
                note="Initialized when creating product unit",
            )
        )


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
    if "status_code" in payload:
        payload["status_code"] = _normalize_status_code(payload["status_code"])

    _validate_category_id(db, product_create.category_id)
    _validate_units_payload(db, units_payload)

    new_product = Product(**payload) # **dict展開，會建立新物件

    db.add(new_product)
    db.flush()

    for item in units_payload:
        db.add(ProductUnits(product_id=new_product.id, **item))
        _ensure_inventory_balance_for_unit(
            db,
            product_id=new_product.id,
            unit_id=item["unit_id"],
            initial_stock=item.get("stock", 0),
        )

    db.commit()
    return get_product_by_id(db, new_product.id) or new_product


def update_product(db:Session, product_id:uuid.UUID, product_update:ProductUpdate) -> Product | None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    payload = product_update.model_dump(exclude_unset=True, exclude={"category_name", "images"}) # 只保留有的欄位(部分更新 且沒有的欄位不會被覆蓋)
    units_payload = payload.pop("units", None)

    if "status_code" in payload:
        payload["status_code"] = _normalize_status_code(payload["status_code"])

    if "category_id" in payload:
        _validate_category_id(db, payload["category_id"])

    for field, value in payload.items(): # 改「已存在的物件」
        setattr(product, field, value)

    if units_payload is not None:
        _validate_units_payload(db, units_payload)
        product.product_units.clear()
        db.flush()
        for item in units_payload:
            product.product_units.append(ProductUnits(**item))
            _ensure_inventory_balance_for_unit(
                db,
                product_id=product.id,
                unit_id=item["unit_id"],
                initial_stock=item.get("stock", 0),
            )

    db.commit() # 寫進資料庫
    return get_product_by_id(db, product.id) or product

def delete_product(db:Session, product_id:uuid.UUID) -> None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    product.status_code = StatusCode.DELETED.value
    db.commit()