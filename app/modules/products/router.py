import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.products import service
from app.modules.products.schema import ProductCreate, ProductResponse, ProductUpdate


router = APIRouter(prefix="/products", tags=["Products"])

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return service.create_product_service(db, payload)

@router.get("", response_model=list[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.list_products_service(db, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = service.get_product_service(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = service.update_product_service(db, product_id, payload)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted = service.delete_product_service(db, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return None