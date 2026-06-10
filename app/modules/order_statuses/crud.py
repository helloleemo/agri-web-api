from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.order_statuses.model import OrderStatus


def get_order_status_by_code(db: Session, code: int) -> OrderStatus | None:
    stmt = select(OrderStatus).where(OrderStatus.code == code)
    return db.scalar(stmt)


def get_order_statuses(db: Session) -> list[OrderStatus]:
    stmt = select(OrderStatus).order_by(OrderStatus.code.asc())
    return list(db.scalars(stmt).all())
