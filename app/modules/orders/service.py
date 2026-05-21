import uuid

from sqlalchemy.orm import Session

from app.modules.orders import crud
from app.modules.orders.model import Order
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate
from app.modules.statuses.utils import get_status_code_by_id


def _to_order_response(db: Session, order: Order) -> OrderResponse:
	order_status_code = get_status_code_by_id(db, order.status_id)
	if order_status_code is None:
		raise ValueError("Order status is invalid")

	items = []
	for item in order.items:
		item_status_code = get_status_code_by_id(db, item.status_id)
		if item_status_code is None:
			raise ValueError("Order item status is invalid")

		items.append({
			"id": item.id,
			"order_id": item.order_id,
			"product_id": item.product_id,
			"quantity": item.quantity,
			"status_id": item_status_code,
			"product_name": getattr(item, "product_name", None),
		})

	return OrderResponse(
		id=order.id,
		user_id=order.user_id,
		status_id=order_status_code,
		created_at=order.created_at,
		updated_at=order.updated_at,
		items=items,
	)


def create_order(db: Session, data: OrderCreate) -> OrderResponse:
	order = crud.create_order(db, data)
	return _to_order_response(db, order)


def get_order_by_id(db: Session, order_id: uuid.UUID) -> OrderResponse | None:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return None
	return _to_order_response(db, order)


def list_orders(db: Session, skip: int = 0, limit: int = 10) -> list[OrderResponse]:
	orders = crud.get_orders(db, skip=skip, limit=limit)
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
