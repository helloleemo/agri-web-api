import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.common.errors import raise_not_found_product
from app.modules.common.messages import ProductMessages
from app.modules.common.schema import ApiResponse
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.products import service
from app.modules.products.schema import ProductCreate, ProductResponse, ProductUpdate
from app.modules.roles.constants import RoleCode


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
    pagination: Pagination = Depends(pagination_dep),
    db: Session = Depends(get_db)
):
    products = service.list_products(db, skip=pagination.skip, limit=pagination.limit)
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
        dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
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
        dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
    )
def update_product(
    payload:ProductUpdate,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    update_product = service.update_product(db, product_id, payload)
    if not update_product:
        return raise_not_found_product(str(product_id))
    
    return ok(update_product, ProductMessages.UPDATE)

@router.delete(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
    
)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted_product = service.delete_product(db, product_id)
    return deleted(deleted_product, ProductMessages.DELETE)