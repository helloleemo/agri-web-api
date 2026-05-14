import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.common.schema import ApiResponse
from app.modules.products import service
from app.modules.products.schema import ProductCreate, ProductResponse, ProductUpdate

from app.modules.common.response import ok
from app.modules.common.response import created
from app.modules.common.response import deleted
from app.modules.common.errors import raise_not_found

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=ApiResponse[list[ProductResponse]])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    products = service.list_products(db, skip=skip, limit=limit)
    return ok(products, "products fetched")

@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = service.get_product(db, product_id)
    if not product:
        raise_not_found("PRODUCT_NOT_FOUND", "Product not found")

    return ok(product, "product fetched")
