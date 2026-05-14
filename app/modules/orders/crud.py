import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schema import OrderCreate, OrderUpdate


def get_order_by_id(db: Session, order_id: uuid.UUID) -> Order | None:
	stmt = (
		select(Order)
		.where(Order.id == order_id, Order.status_id != 3)
		.options(selectinload(Order.items))
	)
	return db.scalar(stmt)


def get_orders(db: Session, skip: int = 0, limit: int = 10) -> list[Order]:
	stmt = (
		select(Order)
		.where(Order.status_id != 3)
		.options(selectinload(Order.items))
		.offset(skip)
		.limit(limit)
	)
	return list(db.scalars(stmt).all())


def create_order(db: Session, order_create: OrderCreate) -> Order:
	payload = order_create.model_dump(exclude={"items"})
	new_order = Order(**payload)
	db.add(new_order)
	db.flush()

	for item_data in order_create.items:
		new_item = OrderItem(order_id=new_order.id, **item_data.model_dump())
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

	for field, value in payload.items():
		setattr(order, field, value)

	if items is not None:
		order.items = [OrderItem(order_id=order.id, **item) for item in items]

	db.commit()
	db.refresh(order)
	return order


def delete_order(db: Session, order: Order) -> None:
	order.status_id = 3
	for item in order.items:
		item.status_id = 3
	db.commit()
