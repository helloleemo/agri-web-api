

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.categories.model import Category
from app.modules.categories.schema import CreateCategory, UpdateCategory


def get_category_by_id(db: Session, category_id: uuid.UUID) -> Category | None:
    stmt = (
        select(Category)
        .where(Category.id == category_id)
        .options(selectinload(Category.products))
    )
    return db.scalar(stmt)

def get_categories(db:Session) -> list[Category]:
    stmt = select(Category)
    
    return list(db.scalars(stmt).all())

def create_category(db:Session, category_create:CreateCategory) -> Category:
    payload = category_create.model_dump()
    new_category = Category(**payload)

    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

def update_category(db:Session, category_id:uuid.UUID, category_update:UpdateCategory) -> Category | None:
    category = get_category_by_id(db, category_id)
    if not category:
        return None

    payload = category_update.model_dump(exclude_unset=True)

    for field, value in payload.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category

def delete_category(db:Session, category_id:uuid.UUID) -> bool:
    category = get_category_by_id(db, category_id)
    if not category:
        return False

    db.delete(category)
    db.commit()
    return True