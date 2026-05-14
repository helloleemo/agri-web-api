import uuid

from sqlalchemy.orm import Session

from app.modules.orders import crud
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate


def create_order(db: Session, data: OrderCreate) -> OrderResponse:
	order = crud.create_order(db, data)
	return OrderResponse.model_validate(order)


def get_order_by_id(db: Session, order_id: uuid.UUID) -> OrderResponse | None:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return None
	return OrderResponse.model_validate(order)


def list_orders(db: Session, skip: int = 0, limit: int = 10) -> list[OrderResponse]:
	orders = crud.get_orders(db, skip=skip, limit=limit)
	return [OrderResponse.model_validate(order) for order in orders]


def update_order(db: Session, order_id: uuid.UUID, data: OrderUpdate) -> OrderResponse | None:
	order = crud.update_order(db, order_id, data)
	if not order:
		return None
	return OrderResponse.model_validate(order)


def delete_order(db: Session, order_id: uuid.UUID) -> bool:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return False
	crud.delete_order(db, order)
	return True
