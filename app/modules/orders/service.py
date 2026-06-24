import uuid
import os
from datetime import datetime, timezone
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.auth.service import send_email
from app.modules.coupons import service as coupons_service
from app.modules.orders import crud
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.orders.constants import DeliveryMethodCode, PaymentMethodCode
from app.modules.orders.email_templates import (
	build_admin_bank_transfer_last5_email,
	build_admin_order_status_email,
	build_customer_order_status_email,
)
from app.modules.order_statuses import crud as order_statuses_crud
from app.modules.common.pagination import Pagination
from app.modules.inventories import service as inventories_service
from app.modules.order_statuses.constants import OrderStatusCode
from app.modules.orders.model import Order
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate
from app.modules.products.model import Product, ProductUnits
from app.modules.roles.constants import RoleCode
from app.modules.statuses.constants import StatusCode
from app.modules.notifications.service import build_order_summary_message, get_line_notification_targets, send_line_message
from app.modules.users.model import User


ORDER_NO_PREFIX = "OC"
ORDER_NO_SEQUENCE_LENGTH = 6
GUEST_USER_EMAIL = os.getenv("GUEST_USER_EMAIL", "guest-order@agri.local")
GUEST_USER_NAME = os.getenv("GUEST_USER_NAME", "guest-order")
HOME_DELIVERY_SHIPPING_FEE = 120
ORDER_ITEM_INVALID_ERROR = cast(ErrorCode, ErrorCode.ORDER_ITEM_INVALID)
RESERVED_STATUS_CODES = {
	OrderStatusCode.ORDER_CREATED.value,
	OrderStatusCode.ORDER_CONFIRMED_AND_PENDING_PAYMENT.value,
	OrderStatusCode.PAID_AND_PREPARING.value,
	OrderStatusCode.SHIPPING.value,
}


def _validate_order_status_transition(previous_status_code: int, new_status_code: int) -> None:
	# Once inventory is committed on delivered, reverting would require explicit restock logic.
	if (
		previous_status_code == OrderStatusCode.DELIVERED.value
		and new_status_code != OrderStatusCode.DELIVERED.value
	):
		raise_error(
			ErrorCode.ORDER_INVALID_STATUS,
			detail="Delivered orders cannot be moved back to previous statuses",
		)


def _get_customer_order_notification_recipients(order: Order):
	primary_orderer_email = order.orderer_email or order.customer_email
	recipients = [primary_orderer_email]
	if order.customer_email != primary_orderer_email:
		recipients.append(order.customer_email)
	return list(dict.fromkeys(recipients))


def _get_admin_order_notification_recipients(db: Session):
	staff_admin_emails = db.scalars(
		select(User.email).where(
			User.role_code.in_([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]),
			User.status_code == StatusCode.ENABLED.value,
		)
	).all()
	return list(dict.fromkeys(staff_admin_emails))


def _send_order_status_notification(db: Session, order: Order) -> None:
	order_status = order_statuses_crud.get_order_status_by_code(db, order.order_status_code)
	status_name = order_status.name if order_status else str(order.order_status_code)
	customer_subject, customer_body = build_customer_order_status_email(
		order,
		status_name,
		subject_template=getattr(order_status, "customer_email_subject_template", None),
		body_template=getattr(order_status, "customer_email_body_template", None),
	)
	admin_subject, admin_body = build_admin_order_status_email(
		order,
		status_name,
		subject_template=getattr(order_status, "admin_email_subject_template", None),
		body_template=getattr(order_status, "admin_email_body_template", None),
	)

	for recipient in _get_customer_order_notification_recipients(order):
		send_email(recipient, customer_subject, customer_body)

	for recipient in _get_admin_order_notification_recipients(db):
		send_email(recipient, admin_subject, admin_body)

	line_message = build_order_summary_message(
		order_no=order.order_no,
		status_name=status_name,
		order_status_code=order.order_status_code,
		customer_email=order.customer_email,
		customer_name=order.customer_name,
		created_at=order.created_at.isoformat() if order.created_at else "",
		updated_at=order.updated_at.isoformat() if order.updated_at else "",
		items=[
			{
				"product_name": getattr(getattr(item, "product", None), "name", None),
				"quantity": item.quantity,
			}
			for item in order.items
		],
	)
	for target_id in get_line_notification_targets():
		send_line_message(target_id, line_message)


def _send_bank_transfer_last5_notification(db: Session, order: Order) -> None:
	subject, body = build_admin_bank_transfer_last5_email(order)
	for recipient in _get_admin_order_notification_recipients(db):
		send_email(recipient, subject, body)


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
	product_ids = [item.product_id for item in order.items]
	unit_price_rows = db.execute(
		select(ProductUnits.product_id, ProductUnits.unit_id, ProductUnits.price).where(
			ProductUnits.product_id.in_(product_ids)
		)
	).all() if product_ids else []
	unit_price_map = {
		(row.product_id, row.unit_id): row.price
		for row in unit_price_rows
	}
	for item in order.items:
		product = getattr(item, "product", None)
		unit_price = unit_price_map.get((item.product_id, item.unit_id))
		if unit_price is None:
			unit_price = getattr(product, "price", None)
		items.append({
			"id": item.id,
			"order_id": item.order_id,
			"product_id": item.product_id,
			"unit_id": item.unit_id,
			"quantity": item.quantity,
			"unit": item.unit,
			"unit_price": unit_price,
			"product_name": getattr(product, "name", None),
		})

	return OrderResponse(
		id=order.id,
		order_no=order.order_no,
		customer_email=order.customer_email,
		customer_name=order.customer_name,
		address=order.address,
		coupon_code=order.coupon_code,
		delivery_method=DeliveryMethodCode(order.delivery_method),
		payment_method=PaymentMethodCode(order.payment_method),
		orderer_name=order.orderer_name,
		orderer_phone=order.orderer_phone,
		orderer_email=order.orderer_email,
		subtotal_amount=order.subtotal_amount,
		discount_amount=order.discount_amount,
		shipping_fee=order.shipping_fee,
		manual_adjustment_amount=order.manual_adjustment_amount,
		total_amount=order.total_amount,
		bank_transfer_last5=order.bank_transfer_last5,
		user_id=order.user_id,
		status_code=order.status_code,
		order_status_code=order.order_status_code,
		order_status_name=getattr(getattr(order, "order_status", None), "name", None),
		delivery_method_label=DeliveryMethodCode.label(order.delivery_method),
		payment_method_label=PaymentMethodCode.label(order.payment_method),
		created_at=order.created_at,
		updated_at=order.updated_at,
		items=items,
		user_name=getattr(getattr(order, "user", None), "user_name", None),
		admin_note=order.admin_note,
	)


def _validate_order_items_inventory(db: Session, data: OrderCreate) -> None:
	"""Validate that all order items have inventory balance records before creating the order."""
	from app.modules.inventories import crud as inventories_crud
	
	for item in data.items:
		if item.unit_id is None:
			raise_error(
				ErrorCode.BAD_REQUEST,
				detail=f"Order item requires unit_id for product_id={item.product_id}",
			)
		balance = inventories_crud.get_inventory_balance(db, item.product_id, item.unit_id)
		if balance is None:
			raise_error(
				ErrorCode.BAD_REQUEST,
				detail=f"Inventory balance not found for product_id={item.product_id}, unit_id={item.unit_id}",
			)


def _calculate_order_subtotal(db: Session, data: OrderCreate) -> int:
	product_ids = [item.product_id for item in data.items]
	products = db.scalars(select(Product).where(Product.id.in_(product_ids))).all()
	product_price_map = {product.id: product.price for product in products}
	unit_price_rows = db.execute(
		select(ProductUnits.product_id, ProductUnits.unit_id, ProductUnits.price).where(
			ProductUnits.product_id.in_(product_ids)
		)
	).all()
	unit_price_map = {
		(row.product_id, row.unit_id): row.price
		for row in unit_price_rows
	}

	if len(product_price_map) != len(set(product_ids)):
		raise_error(ORDER_ITEM_INVALID_ERROR, detail="Some order items reference missing products")

	subtotal = 0
	for item in data.items:
		price = unit_price_map.get((item.product_id, item.unit_id))
		if price is None:
			price = product_price_map.get(item.product_id)
		if price is None:
			raise_error(ORDER_ITEM_INVALID_ERROR, detail=f"Missing product price for product_id: {item.product_id}")
		subtotal += price * item.quantity
	return subtotal


def _calculate_shipping_fee(delivery_method: DeliveryMethodCode | int) -> int:
	method_value = int(delivery_method)
	if method_value == DeliveryMethodCode.HOME_DELIVERY.value:
		return HOME_DELIVERY_SHIPPING_FEE
	return 0


def _calculate_total_amount(
	subtotal_amount: int,
	discount_amount: int,
	shipping_fee: int,
	manual_adjustment_amount: int,
) -> int:
	return max(0, subtotal_amount - discount_amount + shipping_fee + manual_adjustment_amount)


def _calculate_subtotal_from_items(
	db: Session,
	*,
	items: list[dict[str, Any]],
) -> int:
	product_ids = [item["product_id"] for item in items]
	products = db.scalars(select(Product).where(Product.id.in_(product_ids))).all()
	product_price_map = {product.id: product.price for product in products}
	unit_price_rows = db.execute(
		select(ProductUnits.product_id, ProductUnits.unit_id, ProductUnits.price).where(
			ProductUnits.product_id.in_(product_ids)
		)
	).all()
	unit_price_map = {
		(row.product_id, row.unit_id): row.price
		for row in unit_price_rows
	}

	if len(product_price_map) != len(set(product_ids)):
		raise_error(ORDER_ITEM_INVALID_ERROR, detail="Some order items reference missing products")

	subtotal = 0
	for item in items:
		product_id = item["product_id"]
		unit_id = item.get("unit_id")
		quantity_value = item.get("quantity")
		if not isinstance(quantity_value, int):
			raise_error(ORDER_ITEM_INVALID_ERROR, detail=f"Invalid quantity for product_id: {product_id}")
		quantity = quantity_value
		price = unit_price_map.get((product_id, unit_id))
		if price is None:
			price = product_price_map.get(product_id)
		if price is None:
			raise_error(ORDER_ITEM_INVALID_ERROR, detail=f"Missing product price for product_id: {product_id}")
		subtotal += price * quantity
	return subtotal


def create_order(db: Session, data: OrderCreate) -> OrderResponse:
	# Validate inventory balance records exist before proceeding
	_validate_order_items_inventory(db, data)
	
	subtotal_amount = _calculate_order_subtotal(db, data)
	discount_amount = 0
	coupon_code = None
	shipping_fee = _calculate_shipping_fee(data.delivery_method)
	manual_adjustment_amount = 0

	if data.coupon_code:
		coupon, discount_amount = coupons_service.apply_coupon(db, data.coupon_code, subtotal_amount)
		coupon_code = coupon.code

	total_amount = _calculate_total_amount(
		subtotal_amount,
		discount_amount,
		shipping_fee,
		manual_adjustment_amount,
	)
	data = data.model_copy(
		update={
			"coupon_code": coupon_code,
			"subtotal_amount": subtotal_amount,
			"discount_amount": discount_amount,
			"shipping_fee": shipping_fee,
			"manual_adjustment_amount": manual_adjustment_amount,
			"total_amount": total_amount,
		}
	)

	order_no = _generate_order_no(db)
	order = crud.create_order(db, data, order_no=order_no)
	inventories_service.apply_order_status_transition(
		db,
		order=order,
		previous_status_code=None,
		new_status_code=order.order_status_code,
		operator_user_id=order.user_id,
	)
	db.commit()
	db.refresh(order)
	if order.order_status_code == OrderStatusCode.ORDER_CREATED.value:
		_send_order_status_notification(db, order)
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


def update_order(
	db: Session,
	order_id: uuid.UUID,
	data: OrderUpdate,
	*,
	can_manage_all_orders: bool = False,
	operator_user_id: uuid.UUID | None = None,
) -> OrderResponse | None:
	existing_order = crud.get_order_by_id(db, order_id)
	if not existing_order:
		return None
	previous_order_status_code = existing_order.order_status_code
	target_order_status_code = data.order_status_code or previous_order_status_code
	_validate_order_status_transition(previous_order_status_code, target_order_status_code)

	if not can_manage_all_orders:
		if data.items is not None:
			if target_order_status_code == previous_order_status_code:
				raise_error(
					ErrorCode.BAD_REQUEST,
					detail="Updating order items without changing order_status_code is not allowed after inventory tracking is enabled",
				)
		if (
			data.subtotal_amount is not None
			or data.discount_amount is not None
			or data.shipping_fee is not None
			or data.manual_adjustment_amount is not None
			or data.total_amount is not None
		):
			raise_error(ErrorCode.FORBIDDEN, detail="Only admin/staff can adjust order amounts")
		if data.bank_transfer_last5 is not None:
			raise_error(ErrorCode.FORBIDDEN, detail="Use payment reference endpoint to submit transfer last-5")

	if can_manage_all_orders and data.subtotal_amount is not None:
		raise_error(ErrorCode.BAD_REQUEST, detail="subtotal_amount is derived from order items and cannot be edited directly")
	if can_manage_all_orders and data.total_amount is not None:
		raise_error(
			ErrorCode.BAD_REQUEST,
			detail="total_amount is derived from subtotal_amount, discount_amount, shipping_fee, and manual_adjustment_amount",
		)

	payload_updates: dict[str, int] = {}

	if data.items is not None:
		items_payload = [item.model_dump(mode="python") for item in data.items]
		subtotal_from_items = _calculate_subtotal_from_items(db, items=items_payload)
		payload_updates["subtotal_amount"] = subtotal_from_items

	if data.delivery_method is not None:
		payload_updates["shipping_fee"] = _calculate_shipping_fee(data.delivery_method)

	if can_manage_all_orders:
		if data.discount_amount is not None:
			payload_updates["discount_amount"] = data.discount_amount
		if data.shipping_fee is not None:
			payload_updates["shipping_fee"] = data.shipping_fee
		if data.manual_adjustment_amount is not None:
			payload_updates["manual_adjustment_amount"] = data.manual_adjustment_amount

	should_recompute_total = bool(payload_updates)
	if should_recompute_total:
		final_subtotal = payload_updates["subtotal_amount"] if "subtotal_amount" in payload_updates else existing_order.subtotal_amount
		final_discount = payload_updates["discount_amount"] if "discount_amount" in payload_updates else existing_order.discount_amount
		final_shipping = payload_updates["shipping_fee"] if "shipping_fee" in payload_updates else existing_order.shipping_fee
		final_adjustment = (
			payload_updates["manual_adjustment_amount"]
			if "manual_adjustment_amount" in payload_updates
			else existing_order.manual_adjustment_amount
		)
		payload_updates["total_amount"] = _calculate_total_amount(
			final_subtotal,
			final_discount,
			final_shipping,
			final_adjustment,
		)

	if payload_updates:
		data = data.model_copy(update=payload_updates)

	should_resync_reserved_inventory = (
		data.items is not None
		and can_manage_all_orders
		and target_order_status_code == previous_order_status_code
		and previous_order_status_code in RESERVED_STATUS_CODES
	)

	if should_resync_reserved_inventory:
		inventories_service.apply_order_status_transition(
			db,
			order=existing_order,
			previous_status_code=previous_order_status_code,
			new_status_code=OrderStatusCode.CANCELED.value,
			operator_user_id=operator_user_id or existing_order.user_id,
		)

	order = crud.update_order(db, order_id, data)
	if not order:
		return None

	if should_resync_reserved_inventory:
		inventories_service.apply_order_status_transition(
			db,
			order=order,
			previous_status_code=None,
			new_status_code=order.order_status_code,
			operator_user_id=operator_user_id or existing_order.user_id,
		)
	else:
		inventories_service.apply_order_status_transition(
			db,
			order=order,
			previous_status_code=previous_order_status_code,
			new_status_code=order.order_status_code,
			operator_user_id=operator_user_id or existing_order.user_id,
		)
	db.commit()
	db.refresh(order)
	if order.order_status_code != previous_order_status_code:
		_send_order_status_notification(db, order)
	return _to_order_response(db, order)


def update_bank_transfer_last5(
	db: Session,
	order_id: uuid.UUID,
	*,
	bank_transfer_last5: str,
) -> OrderResponse | None:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return None

	if order.order_status_code != OrderStatusCode.ORDER_CONFIRMED_AND_PENDING_PAYMENT.value:
		raise_error(ErrorCode.BAD_REQUEST, detail="Only pending-payment orders can submit transfer last-5")

	if order.payment_method != PaymentMethodCode.BANK_TRANSFER.value:
		raise_error(ErrorCode.BAD_REQUEST, detail="Only bank-transfer orders can submit transfer last-5")

	order.bank_transfer_last5 = bank_transfer_last5
	db.commit()
	db.refresh(order)
	_send_bank_transfer_last5_notification(db, order)
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

	previous_order_status_code = order.order_status_code
	_validate_order_status_transition(previous_order_status_code, OrderStatusCode.CANCELED.value)
	updated = crud.cancel_order(db, order, OrderStatusCode.CANCELED.value)
	inventories_service.apply_order_status_transition(
		db,
		order=updated,
		previous_status_code=previous_order_status_code,
		new_status_code=updated.order_status_code,
		operator_user_id=order.user_id,
	)
	db.commit()
	db.refresh(updated)
	if updated.order_status_code != previous_order_status_code:
		_send_order_status_notification(db, updated)
	return _to_order_response(db, updated)


def update_admin_note(db: Session, order_id: uuid.UUID, note: str | None) -> OrderResponse | None:
	order = crud.get_order_by_id(db, order_id)
	if not order:
		return None
	updated = crud.update_admin_note(db, order, note)
	return _to_order_response(db, updated)
