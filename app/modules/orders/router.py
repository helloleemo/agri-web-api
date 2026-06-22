import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import AuthUser, get_auth_context, get_optional_auth_context
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error, raise_not_found_order
from app.modules.common.messages import OrderMessages
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.common.response import created, deleted, ok
from app.modules.common.schema import ApiResponse
from app.modules.orders import service
from app.modules.orders.schema import (
	OrderAdminNoteUpdate,
	OrderCreate,
	OrderPaymentReferenceUpdate,
	OrderResponse,
	OrderUpdate,
)
from app.modules.roles.constants import RoleCode

router = APIRouter(prefix="/orders", tags=["Orders"])


ADMIN_STAFF_ROLE_CODES = {RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value}


def _can_manage_all_orders(auth: AuthUser) -> bool:
	return auth.role_code in ADMIN_STAFF_ROLE_CODES


def _ensure_can_access_order(auth: AuthUser, owner_id: uuid.UUID, action: str) -> None:
	if not _can_manage_all_orders(auth) and owner_id != auth.id:
		raise_error(ErrorCode.FORBIDDEN, detail=f"You can only {action} your own orders")



@router.get("", 
			response_model=ApiResponse[list[OrderResponse]], 
			response_model_exclude_none=True,
		)
def list_orders(
	pagination: Pagination = Depends(pagination_dep),
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	user_id = None if _can_manage_all_orders(auth) else auth.id
	orders = service.list_orders(db, skip=pagination.skip, limit=pagination.limit, user_id=user_id)
	if not _can_manage_all_orders(auth):
		orders = [o.model_copy(update={'admin_note': None}) for o in orders]
	return ok(orders, OrderMessages.LIST)


@router.get(
		"/query",
		response_model=ApiResponse[OrderResponse],
		response_model_exclude_none=True,
	)
def query_order_by_no_and_email(
	order_no: str = Query(..., min_length=1, max_length=20),
	email: str = Query(..., min_length=3, max_length=120),
	auth: AuthUser | None = Depends(get_optional_auth_context),
	db: Session = Depends(get_db),
):
	if auth is not None and auth.role_code == RoleCode.ROLE_MEMBER.value and email != auth.email:
		raise_error(ErrorCode.FORBIDDEN, detail="Members can only query orders with their own email")

	order = service.get_order_by_order_no_and_email(db, order_no=order_no, customer_email=email)
	if not order:
		raise_not_found_order(order_no)

	return ok(order.model_copy(update={'admin_note': None}), OrderMessages.GET)


@router.get(
		"/{order_id}", 
		response_model=ApiResponse[OrderResponse], 
		response_model_exclude_none=True,
	)
def get_order(
	order_id: uuid.UUID,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	order = service.get_order_by_id(db, order_id)
	if not order:
		raise_not_found_order(str(order_id))

	_ensure_can_access_order(auth, order.user_id, "view")

	if not _can_manage_all_orders(auth):
		order = order.model_copy(update={'admin_note': None})
	return ok(order, OrderMessages.GET)


@router.post("", response_model=ApiResponse[OrderResponse], status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_order(
	payload: OrderCreate,
	auth: AuthUser | None = Depends(get_optional_auth_context),
	db: Session = Depends(get_db),
):
	if auth is None:
		if payload.user_id is not None:
			raise_error(ErrorCode.FORBIDDEN, detail="Guest cannot assign user_id")
		payload = payload.model_copy(update={"user_id": service.get_or_create_guest_user_id(db)})
	else:
		if _can_manage_all_orders(auth):
			resolved_user_id = payload.user_id or auth.id
		else:
			resolved_user_id = auth.id
			if payload.customer_email != auth.email:
				raise_error(ErrorCode.FORBIDDEN, detail="Members can only create orders with their own email")
		payload = payload.model_copy(update={"user_id": resolved_user_id})

	order = service.create_order(db, payload)
	return created(order, OrderMessages.CREATE)


@router.patch("/{order_id}/admin-note", response_model=ApiResponse[OrderResponse], response_model_exclude_none=True)
def update_order_admin_note(
	order_id: uuid.UUID,
	payload: OrderAdminNoteUpdate,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	if not _can_manage_all_orders(auth):
		raise_error(ErrorCode.FORBIDDEN, detail="Only admin/staff can update admin notes")

	existing = service.get_order_by_id(db, order_id)
	if not existing:
		raise_not_found_order(str(order_id))

	updated = service.update_admin_note(db, order_id, payload.admin_note)
	if not updated:
		raise_not_found_order(str(order_id))

	return ok(updated, OrderMessages.ADMIN_NOTE_UPDATE)


@router.patch("/{order_id}", response_model=ApiResponse[OrderResponse], response_model_exclude_none=True)
def update_order(
	order_id: uuid.UUID,
	payload: OrderUpdate,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	existing = service.get_order_by_id(db, order_id)
	if not existing:
		raise_not_found_order(str(order_id))

	_ensure_can_access_order(auth, existing.user_id, "update")

	order = service.update_order(
		db,
		order_id,
		payload,
		can_manage_all_orders=_can_manage_all_orders(auth),
		operator_user_id=auth.id,
	)
	if not order:
		raise_not_found_order(str(order_id))

	return ok(order, OrderMessages.UPDATE)


@router.patch("/{order_id}/bank-transfer-last5", response_model=ApiResponse[OrderResponse], response_model_exclude_none=True)
def update_order_bank_transfer_last5(
	order_id: uuid.UUID,
	payload: OrderPaymentReferenceUpdate,
	auth: AuthUser | None = Depends(get_optional_auth_context),
	db: Session = Depends(get_db),
):
	existing = service.get_order_by_id(db, order_id)
	if not existing:
		raise_not_found_order(str(order_id))

	if auth is None:
		if not payload.customer_email or payload.customer_email.lower() != existing.customer_email.lower():
			raise_error(ErrorCode.FORBIDDEN, detail="Guest must provide matching customer_email")
	else:
		_ensure_can_access_order(auth, existing.user_id, "update")

	updated = service.update_bank_transfer_last5(
		db,
		order_id,
		bank_transfer_last5=payload.bank_transfer_last5,
	)
	if not updated:
		raise_not_found_order(str(order_id))

	is_manage_all = _can_manage_all_orders(auth) if auth else False
	if not is_manage_all:
		updated = updated.model_copy(update={"admin_note": None})

	return ok(updated, OrderMessages.UPDATE)


@router.patch("/{order_id}/cancel", response_model=ApiResponse[OrderResponse], response_model_exclude_none=True)
def cancel_order(
	order_id: uuid.UUID,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	existing = service.get_order_by_id(db, order_id)
	if not existing:
		raise_not_found_order(str(order_id))

	_ensure_can_access_order(auth, existing.user_id, "cancel")

	canceled = service.cancel_order(db, order_id)
	if not canceled:
		raise_not_found_order(str(order_id))

	return ok(canceled, OrderMessages.CANCEL)


@router.delete("/{order_id}", response_model=ApiResponse[dict[str, str]], response_model_exclude_none=True)
def delete_order(
	order_id: uuid.UUID,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	if auth.role_code == RoleCode.ROLE_STAFF.value:
		raise_error(ErrorCode.FORBIDDEN, detail="Staff cannot delete orders")

	existing = service.get_order_by_id(db, order_id)
	if not existing:
		raise_not_found_order(str(order_id))

	_ensure_can_access_order(auth, existing.user_id, "delete")

	is_deleted = service.delete_order(db, order_id)
	if not is_deleted:
		raise_not_found_order(str(order_id))

	return deleted(str(order_id), OrderMessages.DELETE)
