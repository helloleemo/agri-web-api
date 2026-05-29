import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.statuses.constants import STATUS_CODE_DELETED, STATUS_CODE_ENABLED
from app.modules.statuses.utils import get_status_id_by_code
from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schema import OrderCreate, OrderUpdate


def get_order_by_id(db: Session, order_id: uuid.UUID) -> Order | None:
	deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
	conditions = [Order.id == order_id]
	if deleted_status_id is not None:
		conditions.append(Order.status_id != deleted_status_id)

	stmt = (
		select(Order)
		.where(*conditions)
		.options(selectinload(Order.items))
	)
	return db.scalar(stmt)


def get_orders(
	db: Session,
	skip: int = 0,
	limit: int = 10,
	user_id: uuid.UUID | None = None,
) -> list[Order]:
	deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
	conditions = []
	if deleted_status_id is not None:
		conditions.append(Order.status_id != deleted_status_id)
	if user_id is not None:
		conditions.append(Order.user_id == user_id)

	stmt = (
		select(Order)
		.where(*conditions)
		.options(selectinload(Order.items))
		.offset(skip)
		.limit(limit)
	)
	return list(db.scalars(stmt).all())


def create_order(db: Session, order_create: OrderCreate) -> Order:
	payload = order_create.model_dump(exclude={"items"})
	order_status_code = payload.pop("status_id", STATUS_CODE_ENABLED)
	order_status_id = get_status_id_by_code(db, order_status_code)
	if order_status_id is None:
		raise ValueError(f"Status code {order_status_code} is not configured")
	payload["status_id"] = order_status_id

	new_order = Order(**payload)
	db.add(new_order)
	db.flush()

	for item_data in order_create.items:
		item_payload = item_data.model_dump()
		item_status_code = item_payload.pop("status_id", STATUS_CODE_ENABLED)
		item_status_id = get_status_id_by_code(db, item_status_code)
		if item_status_id is None:
			raise ValueError(f"Status code {item_status_code} is not configured")
		item_payload["status_id"] = item_status_id
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
	if "status_id" in payload:
		status_id = get_status_id_by_code(db, payload["status_id"])
		if status_id is None:
			raise ValueError(f"Status code {payload['status_id']} is not configured")
		payload["status_id"] = status_id

	for field, value in payload.items():
		setattr(order, field, value)

	if items is not None:
		new_items: list[OrderItem] = []
		for item in items:
			item_status_code = item.get("status_id", STATUS_CODE_ENABLED)
			item_status_id = get_status_id_by_code(db, item_status_code)
			if item_status_id is None:
				raise ValueError(f"Status code {item_status_code} is not configured")
			item["status_id"] = item_status_id
			new_items.append(OrderItem(order_id=order.id, **item))
		order.items = new_items

	db.commit()
	db.refresh(order)
	return order


def delete_order(db: Session, order: Order) -> None:
	deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
	if deleted_status_id is None:
		raise ValueError("Deleted status is not configured")

	order.status_id = deleted_status_id
	for item in order.items:
		item.status_id = deleted_status_id
	db.commit()
