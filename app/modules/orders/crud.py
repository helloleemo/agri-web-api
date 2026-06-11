import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.common.pagination import Pagination
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.order_statuses import crud as order_statuses_crud
from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schema import OrderCreate, OrderUpdate
from app.modules.statuses.constants import StatusCode


def get_order_by_id(db: Session, order_id: uuid.UUID) -> Order | None:
	stmt = (
		select(Order)
		.where(
			Order.id == order_id,
			Order.status_code != StatusCode.DELETED.value,
		)
		.options(selectinload(Order.user))
		.options(selectinload(Order.order_status))
		.options(selectinload(Order.items).selectinload(OrderItem.product))
	)
	return db.scalar(stmt)


def get_order_by_order_no_and_email(db: Session, order_no: str, customer_email: str) -> Order | None:
	stmt = (
		select(Order)
		.where(
			Order.order_no == order_no,
			Order.customer_email == customer_email,
			Order.status_code != StatusCode.DELETED.value,
		)
		.options(selectinload(Order.user))
		.options(selectinload(Order.order_status))
		.options(selectinload(Order.items).selectinload(OrderItem.product))
	)
	return db.scalar(stmt)


def get_orders(
	db: Session,
	pagination: Pagination,
	user_id: uuid.UUID | None = None,
) -> list[Order]:
	stmt = (
		select(Order)
		.where(Order.status_code != StatusCode.DELETED.value)
		.options(selectinload(Order.user))
		.options(selectinload(Order.order_status))
		.options(selectinload(Order.items).selectinload(OrderItem.product))
	)
	if user_id is not None:
		stmt = stmt.where(Order.user_id == user_id)

	stmt = stmt.offset(pagination.skip).limit(pagination.limit)
	return list(db.scalars(stmt).all())


def create_order(db: Session, order_create: OrderCreate, order_no: str) -> Order:
	payload = order_create.model_dump(exclude={"items"})
	payload["order_no"] = order_no
	if not order_statuses_crud.get_order_status_by_code(db, payload["order_status_code"]):
		raise_error(ErrorCode.ORDER_INVALID_STATUS, detail=f"Invalid order_status_code: {payload['order_status_code']}")
	new_order = Order(**payload)
	
	db.add(new_order)
	db.flush()

	for item_data in order_create.items:
		item_payload = item_data.model_dump(exclude={"unit"})
		new_item = OrderItem(order_id=new_order.id, **item_payload)
		db.add(new_item)

	db.commit()
	db.refresh(new_order)
	return new_order


def update_order(db: Session, order_id: uuid.UUID, order_update: OrderUpdate) -> Order | None:
	order = get_order_by_id(db, order_id)
	if not order:
		return None

	payload = order_update.model_dump(exclude_unset=True)
	items = payload.pop("items", None)
	order_status_code = payload.get("order_status_code")
	if order_status_code is not None and not order_statuses_crud.get_order_status_by_code(db, order_status_code):
		raise_error(ErrorCode.ORDER_INVALID_STATUS, detail=f"Invalid order_status_code: {order_status_code}")

	for field, value in payload.items():
		setattr(order, field, value)

	if items is not None:
		order.items = [
			OrderItem(order_id=order.id, **{k: v for k, v in item.items() if k != "unit"})
			for item in items
		]

	db.commit()
	db.refresh(order)
	return order


def delete_order(db: Session, order: Order) -> None:
	order.status_code = StatusCode.DELETED.value
	db.commit()


def cancel_order(db: Session, order: Order, cancel_order_status_code: int) -> Order:
	order.order_status_code = cancel_order_status_code
	db.commit()
	db.refresh(order)
	return order
