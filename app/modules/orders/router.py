import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import AuthUser, get_auth_context
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error, raise_not_found_order
from app.modules.common.messages import OrderMessages
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.common.response import created, deleted, ok
from app.modules.common.schema import ApiResponse
from app.modules.orders import service
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate
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
	return ok(orders, OrderMessages.LIST)


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

	return ok(order, OrderMessages.GET)


@router.post("", response_model=ApiResponse[OrderResponse], status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_order(
	payload: OrderCreate,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	if not _can_manage_all_orders(auth) and payload.user_id != auth.id:
		raise_error(ErrorCode.FORBIDDEN, detail="You can only create your own orders")

	order = service.create_order(db, payload)
	return created(order, OrderMessages.CREATE)


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

	order = service.update_order(db, order_id, payload)
	if not order:
		raise_not_found_order(str(order_id))

	return ok(order, OrderMessages.UPDATE)


@router.delete("/{order_id}", response_model=ApiResponse[dict[str, str]], response_model_exclude_none=True)
def delete_order(
	order_id: uuid.UUID,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	existing = service.get_order_by_id(db, order_id)
	if not existing:
		raise_not_found_order(str(order_id))

	_ensure_can_access_order(auth, existing.user_id, "delete")

	is_deleted = service.delete_order(db, order_id)
	if not is_deleted:
		raise_not_found_order(str(order_id))

	return deleted(str(order_id), OrderMessages.DELETE)
