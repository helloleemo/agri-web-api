import uuid
import os
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.orders import crud
from app.modules.common.pagination import Pagination
from app.modules.order_statuses.constants import OrderStatusCode
from app.modules.orders.model import Order
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate
from app.modules.roles.constants import RoleCode
from app.modules.statuses.constants import StatusCode
from app.modules.users.model import User


ORDER_NO_PREFIX = "OC"
ORDER_NO_SEQUENCE_LENGTH = 6
GUEST_USER_EMAIL = os.getenv("GUEST_USER_EMAIL", "guest-order@agri.local")
GUEST_USER_NAME = os.getenv("GUEST_USER_NAME", "guest-order")


def get_or_create_guest_user_id(db: Session) -> uuid.UUID:
	guest_user = db.scalar(select(User).where(User.email == GUEST_USER_EMAIL))
	if guest_user:
		return guest_user.id

	now = datetime.now(timezone.utc)
	guest_user = User(
		id=uuid.uuid4(),
		email=GUEST_USER_EMAIL,
		user_name=GUEST_USER_NAME,
		password_hash="guest-placeholder",
		role_code=RoleCode.ROLE_MEMBER.value,
		status_code=StatusCode.ENABLED.value,
		email_verified_at=now,
		created_at=now,
		updated_at=now,
	)
	db.add(guest_user)
	db.commit()
	db.refresh(guest_user)
	return guest_user.id


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
		customer_email=order.customer_email,
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


def get_order_by_order_no_and_email(db: Session, order_no: str, customer_email: str) -> OrderResponse | None:
	order = crud.get_order_by_order_no_and_email(db, order_no, customer_email)
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
