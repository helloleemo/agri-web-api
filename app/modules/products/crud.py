import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.common.pagination import Pagination
from app.modules.products.model import Product
from app.modules.products.schema import ProductCreate, ProductUpdate
from app.modules.statuses.constants import StatusCode

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
            selectinload(Product.images))
   ) 
    return db.scalar(stmt)


def get_products(db: Session, pagination: Pagination) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.status_code != StatusCode.DELETED.value)
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return list(db.scalars(stmt).all())

def create_product(db:Session, product_create:ProductCreate) -> Product:
    payload = product_create.model_dump()  # object轉換成可操作的dict

    new_product = Product(**payload) # **dict展開，會建立新物件

    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update_product(db:Session, product_id:uuid.UUID, product_update:ProductUpdate) -> Product | None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    payload = product_update.model_dump(exclude_unset=True) # 只保留有的欄位(部分更新 且沒有的欄位不會被覆蓋)

    for field, value in payload.items(): # 改「已存在的物件」
        setattr(product, field, value)

    db.commit() # 寫進資料庫
    db.refresh(product)  # 重新從 DB 載入 product 最新狀態
    return product # 回傳更新完成後的商品物件

def delete_product(db:Session, product_id:uuid.UUID) -> None:
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    product.status_code = StatusCode.DELETED.value
    db.commit()