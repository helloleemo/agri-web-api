import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.order_statuses.model import OrderStatus
from app.modules.orders.model import Order
from app.modules.statuses.constants import StatusCode


def get_order_status_by_code(db: Session, code: int) -> OrderStatus | None:
    stmt = select(OrderStatus).where(OrderStatus.code == code)
    return db.scalar(stmt)


def get_order_statuses(db: Session) -> list[OrderStatus]:
    stmt = select(OrderStatus).order_by(OrderStatus.code.asc())
    return list(db.scalars(stmt).all())


def get_order_statuses_by_user_id(db: Session, user_id: uuid.UUID) -> list[OrderStatus]:
    stmt = (
        select(OrderStatus)
        .join(Order, Order.order_status_code == OrderStatus.code)
        .where(
            Order.user_id == user_id,
            Order.status_code != StatusCode.DELETED.value,
        )
        .group_by(OrderStatus.id, OrderStatus.code, OrderStatus.name)
        .order_by(OrderStatus.code.asc())
    )
    return list(db.scalars(stmt).all())


def update_order_status_email_templates(
    db: Session,
    *,
    order_status: OrderStatus,
    customer_email_subject_template: str | None,
    customer_email_body_template: str | None,
    admin_email_subject_template: str | None,
    admin_email_body_template: str | None,
) -> OrderStatus:
    order_status.customer_email_subject_template = customer_email_subject_template
    order_status.customer_email_body_template = customer_email_body_template
    order_status.admin_email_subject_template = admin_email_subject_template
    order_status.admin_email_body_template = admin_email_body_template
    db.commit()
    db.refresh(order_status)
    return order_status
