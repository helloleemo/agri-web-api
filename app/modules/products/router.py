import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.common.schema import ApiResponse
from app.modules.products import service
from app.modules.products.schema import ProductCreate, ProductResponse, ProductUpdate


router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=ApiResponse[list[ProductResponse]])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    products = service.list_products(db, skip=skip, limit=limit)
    return ApiResponse[list[ProductResponse]](
        success=True,
        message="products fetched",
        data=products
    )

@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ApiResponse[ProductResponse](
        success=True,
        message="product fetched",
        data=product
    )