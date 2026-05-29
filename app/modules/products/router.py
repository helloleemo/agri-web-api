import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.common.errors import raise_not_found_product
from app.modules.common.messages import ProductMessages
from app.modules.common.schema import ApiResponse
from app.modules.products import service
from app.modules.products.schema import ProductCreate, ProductResponse, ProductUpdate
from app.modules.roles.constants import ROLE_ADMIN, ROLE_STAFF

from app.modules.common.response import ok
from app.modules.common.response import created
from app.modules.common.response import deleted

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    # dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_STAFF]))],
)

@router.get("", response_model=ApiResponse[list[ProductResponse]], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    products = service.list_products(db, skip=skip, limit=limit)
    return ok(products, ProductMessages.LIST)

@router.get("/{product_id}", response_model=ApiResponse[ProductResponse], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = service.get_product(db, product_id)
    if not product:
        raise_not_found_product(str(product_id))

    return ok(product, ProductMessages.GET)

@router.post(
        "", 
        response_model=ApiResponse[ProductResponse], 
        response_model_exclude_none=True, 
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_STAFF]))],
    )
def create_product(
        payload:ProductCreate,
        db: Session = Depends(get_db)
    ):
    created_product = service.create_product(db, payload)
    return created(created_product, ProductMessages.CREATE)
    

@router.put(
        "/{product_id}",
        response_model=ApiResponse[ProductResponse],
        response_model_exclude_none=True,
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_STAFF]))],
    )
def update_product(
    payload:ProductUpdate,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    update_product = service.update_product(db, product_id, payload)
    
    return ok(update_product, ProductMessages.UPDATE)

@router.delete(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_STAFF]))],
)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted_product = service.delete_product(db, product_id)
    return deleted(deleted_product, ProductMessages.DELETE)