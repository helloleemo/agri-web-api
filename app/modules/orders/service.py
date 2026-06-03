import uuid

from sqlalchemy.orm import Session

from app.modules.orders import crud
from app.modules.common.pagination import Pagination
from app.modules.orders.model import Order
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate


def _to_order_response(db: Session, order: Order) -> OrderResponse:
	items = []
	for item in order.items:
		items.append({
			"id": item.id,
			"order_id": item.order_id,
			"product_id": item.product_id,
			"quantity": item.quantity,
			"unit": getattr(item, "unit", None),
			"product_name": getattr(item, "product_name", None),
		})

	return OrderResponse(
		id=order.id,
		user_id=order.user_id,
		status_code=order.status_code,
		created_at=order.created_at,
		updated_at=order.updated_at,
		items=items,
		user_name=getattr(order, "user_name", None),
	)


def create_order(db: Session, data: OrderCreate) -> OrderResponse:
	order = crud.create_order(db, data)
	return _to_order_response(db, order)


def get_order_by_id(db: Session, order_id: uuid.UUID) -> OrderResponse | None:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return None
	return _to_order_response(db, order)


def list_orders(
	db: Session,
	skip: int = 0,
	limit: int = 10,
	user_id: uuid.UUID | None = None,
) -> list[OrderResponse]:
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
