

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.categories import service
from app.modules.categories.schema import CategoryResponse, CreateCategory, UpdateCategory
from app.modules.common.errors import raise_not_found_category
from app.modules.common.messages import CategoryMessages
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.common.response import ok
from app.modules.common.schema import ApiResponse
from app.modules.roles.constants import RoleCode


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.get("", response_model=ApiResponse[list[CategoryResponse]], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
def list_categories(
    pagination: Pagination = Depends(pagination_dep),
    db: Session = Depends(get_db)
):
    categories = service.list_categories(db)
    return ok(categories, CategoryMessages.LIST)

@router.get("/{category_id}", response_model=ApiResponse[CategoryResponse], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
def get_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    category = service.get_category(db, category_id)
    if not category:
        raise_not_found_category(str(category_id))

    return ok(category, CategoryMessages.GET)

@router.post(
    "", response_model=ApiResponse[CategoryResponse], response_model_exclude_none=True, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def create_category(category: CreateCategory, db: Session = Depends(get_db)):
    new_category = service.create_category(db, category)
    return ok(new_category, CategoryMessages.CREATE)

@router.put(
        "/{category_id}",
        response_model=ApiResponse[CategoryResponse],
        response_model_exclude_none=True,
        status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
    )
def update_category(category_id: uuid.UUID, category: UpdateCategory, db: Session = Depends(get_db)):
    updated_category = service.update_category(db, category_id, category)
    if not updated_category:
        raise_not_found_category(str(category_id))
    return ok(updated_category, CategoryMessages.UPDATE)


@router.delete(
        "/{category_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted = service.delete_category(db, category_id)
    if not deleted:
        raise_not_found_category(str(category_id))
    return ok(None, CategoryMessages.DELETE)