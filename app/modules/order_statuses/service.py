import uuid

from sqlalchemy.orm import Session

from app.modules.order_statuses import crud
from app.modules.order_statuses.model import OrderStatus
from app.modules.order_statuses.schema import OrderStatusEmailTemplateUpdate, OrderStatusResponse


def _to_order_status_response(order_status: OrderStatus) -> OrderStatusResponse:
    return OrderStatusResponse(
        id=order_status.id,
        code=order_status.code,
        name=order_status.name,
        customer_email_subject_template=order_status.customer_email_subject_template,
        customer_email_body_template=order_status.customer_email_body_template,
        admin_email_subject_template=order_status.admin_email_subject_template,
        admin_email_body_template=order_status.admin_email_body_template,
    )


def list_order_statuses(db: Session) -> list[OrderStatusResponse]:
    statuses = crud.get_order_statuses(db)
    return [_to_order_status_response(status) for status in statuses]


def list_order_statuses_by_user_id(db: Session, user_id: uuid.UUID) -> list[OrderStatusResponse]:
    statuses = crud.get_order_statuses_by_user_id(db, user_id)
    return [_to_order_status_response(status) for status in statuses]


def get_order_status_by_code(db: Session, code: int) -> OrderStatusResponse | None:
    order_status = crud.get_order_status_by_code(db, code)
    if not order_status:
        return None
    return _to_order_status_response(order_status)


def update_order_status_email_templates(
    db: Session,
    *,
    code: int,
    payload: OrderStatusEmailTemplateUpdate,
) -> OrderStatusResponse | None:
    order_status = crud.get_order_status_by_code(db, code)
    if not order_status:
        return None

    updated = crud.update_order_status_email_templates(
        db,
        order_status=order_status,
        customer_email_subject_template=payload.customer_email_subject_template,
        customer_email_body_template=payload.customer_email_body_template,
        admin_email_subject_template=payload.admin_email_subject_template,
        admin_email_body_template=payload.admin_email_body_template,
    )
    return _to_order_status_response(updated)
