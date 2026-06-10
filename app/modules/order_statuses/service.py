from sqlalchemy.orm import Session

from app.modules.order_statuses import crud
from app.modules.order_statuses.model import OrderStatus
from app.modules.order_statuses.schema import OrderStatusResponse


def _to_order_status_response(order_status: OrderStatus) -> OrderStatusResponse:
    return OrderStatusResponse(
        id=order_status.id,
        code=order_status.code,
        name=order_status.name,
    )


def list_order_statuses(db: Session) -> list[OrderStatusResponse]:
    statuses = crud.get_order_statuses(db)
    return [_to_order_status_response(status) for status in statuses]


def get_order_status_by_code(db: Session, code: int) -> OrderStatusResponse | None:
    order_status = crud.get_order_status_by_code(db, code)
    if not order_status:
        return None
    return _to_order_status_response(order_status)
