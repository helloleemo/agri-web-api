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
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_STAFF]))],
)

@router.get("", response_model=ApiResponse[list[ProductResponse]], response_model_exclude_none=True)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    products = service.list_products(db, skip=skip, limit=limit)
    return ok(products, ProductMessages.LIST)

@router.get("/{product_id}", response_model=ApiResponse[ProductResponse], response_model_exclude_none=True)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = service.get_product(db, product_id)
    if not product:
        raise_not_found_product(str(product_id))

    return ok(product, ProductMessages.GET)
