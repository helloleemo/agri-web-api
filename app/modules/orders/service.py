import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.orders import crud
from app.modules.common.pagination import Pagination
from app.modules.order_statuses.constants import OrderStatusCode
from app.modules.orders.model import Order
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate


ORDER_NO_PREFIX = "OC"
ORDER_NO_SEQUENCE_LENGTH = 6


def _generate_order_no(db: Session) -> str:
	today = db.scalar(select(func.to_char(func.now(), "YYYYMMDD")))
	if not today:
		raise RuntimeError("Failed to generate order number date prefix")
	prefix = f"{ORDER_NO_PREFIX}{today}"
	last_order_no = db.scalar(
		select(Order.order_no)
		.where(Order.order_no.like(f"{prefix}%"))
		.order_by(Order.order_no.desc())
		.limit(1)
	)

	if last_order_no:
		sequence = int(last_order_no[len(prefix):]) + 1
	else:
		sequence = 1

	return f"{prefix}{sequence:0{ORDER_NO_SEQUENCE_LENGTH}d}"


def _to_order_response(db: Session, order: Order) -> OrderResponse:
	items = []
	for item in order.items:
		product = getattr(item, "product", None)
		items.append({
			"id": item.id,
			"order_id": item.order_id,
			"product_id": item.product_id,
			"quantity": item.quantity,
			"unit": None,
			"product_name": getattr(product, "name", None),
		})

	return OrderResponse(
		id=order.id,
		order_no=order.order_no,
		user_id=order.user_id,
		status_code=order.status_code,
		order_status_code=order.order_status_code,
		order_status_name=getattr(getattr(order, "order_status", None), "name", None),
		created_at=order.created_at,
		updated_at=order.updated_at,
		items=items,
		user_name=getattr(getattr(order, "user", None), "user_name", None),
	)


def create_order(db: Session, data: OrderCreate) -> OrderResponse:
	order_no = _generate_order_no(db)
	order = crud.create_order(db, data, order_no=order_no)
	return _to_order_response(db, order)


def get_order_by_id(db: Session, order_id: uuid.UUID) -> OrderResponse | None:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return None
	return _to_order_response(db, order)


def list_orders(
	db: Session,
	skip: int = 0,
	limit: int = 200,
	user_id: uuid.UUID | None = None,
) -> "list[OrderResponse]":
	pagination = Pagination(skip=skip, limit=limit)
	orders = crud.get_orders(db, pagination=pagination, user_id=user_id)
	return [_to_order_response(db, order) for order in orders]


def update_order(db: Session, order_id: uuid.UUID, data: OrderUpdate) -> OrderResponse | None:
	order = crud.update_order(db, order_id, data)
	if not order:
		return None
	return _to_order_response(db, order)


def delete_order(db: Session, order_id: uuid.UUID) -> bool:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return False
	crud.delete_order(db, order)
	return True


def cancel_order(db: Session, order_id: uuid.UUID) -> OrderResponse | None:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return None

	updated = crud.cancel_order(db, order, OrderStatusCode.CANCELED.value)
	return _to_order_response(db, updated)
