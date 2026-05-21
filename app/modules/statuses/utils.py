import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.statuses.model import Status


def get_status_id_by_code(db: Session, status_code: int) -> uuid.UUID | None:
    stmt = select(Status.id).where(Status.code == status_code)
    return db.scalar(stmt)


def get_status_code_by_id(db: Session, status_id: uuid.UUID) -> int | None:
    stmt = select(Status.code).where(Status.id == status_id)
    return db.scalar(stmt)
