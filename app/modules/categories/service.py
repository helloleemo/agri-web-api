

import uuid

from sqlalchemy.orm import Session

from app.modules.categories import crud
from app.modules.categories.model import Category
from app.modules.categories.schema import CategoryResponse, CreateCategory, UpdateCategory
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error


def _to_category_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        meta_data=category.meta_data,
        name=category.name,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )

def create_category(db: Session, data: CreateCategory) -> CategoryResponse:
    existing = crud.get_category_by_name(db, data.name)
    if existing:
        raise_error(ErrorCode.CATEGORY_NAME_ALREADY_EXISTS, detail=f"Category name already exists: {data.name}")
    category = crud.create_category(db, data)
    return _to_category_response(category)

def get_category(db: Session, category_id: uuid.UUID) -> CategoryResponse | None:
    category = crud.get_category_by_id(db, category_id)
    if not category:
        return None
    return _to_category_response(category)

def list_categories(db: Session) -> list[CategoryResponse]:
    categories = crud.get_categories(db)
    return [_to_category_response(category) for category in categories]


def update_category(
    db: Session,
    category_id: uuid.UUID,
    data: UpdateCategory,
) -> CategoryResponse | None:
    existing = crud.get_category_by_name(db, data.name)
    if existing and existing.id != category_id:
        raise_error(ErrorCode.CATEGORY_NAME_ALREADY_EXISTS, detail=f"Category name already exists: {data.name}")

    updated = crud.update_category(db, category_id, data)
    if updated is None:
        return None
    return _to_category_response(updated)


def delete_category(db: Session, category_id: uuid.UUID) -> bool:
    category = crud.get_category_by_id(db, category_id)
    if not category:
        return False
    crud.delete_category(db, category_id)
    return True